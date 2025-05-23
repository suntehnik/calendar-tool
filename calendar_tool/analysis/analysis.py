"""
Calendar analysis functionality.
"""

from datetime import datetime, timedelta, time
import sys
from tabulate import tabulate
from dateutil import tz

# For legacy authentication
from exchangelib import EWSDateTime, EWSTimeZone, CalendarItem, Q

from calendar_tool.auth import auth


def parse_time(time_str):
    """
    Parse time string in HH:MM format.
    
    Args:
        time_str: Time string in HH:MM format
        
    Returns:
        datetime.time: Parsed time object
    """
    hours, minutes = map(int, time_str.split(":"))
    return time(hours, minutes)


def get_calendar_events(account, start_date, end_date, config):
    """
    Get calendar events from Exchange server.
    
    Args:
        account: Authenticated account object
        start_date: Start date for events retrieval
        end_date: End date for events retrieval
        config: Configuration dictionary
        
    Returns:
        list: List of calendar events
    """
    # Use OAuth authentication by default
    use_oauth = config.get("use_oauth", True)
    

    return get_calendar_events(account, start_date, end_date)

def get_calendar_events(account, start_date, end_date):
    """
    Get calendar events using exchangelib (legacy).
    Only includes accepted events and events where user is organizer.
    
    Args:
        account: Authenticated exchangelib account object
        start_date: Start date for events retrieval
        end_date: End date for events retrieval
        
    Returns:
        list: List of calendar events
    """
    try:
        # Use the Exchange time zone from the account
        timezone = account.default_timezone
        
        # Convert dates to EWSDateTime
        start_ews = EWSDateTime.from_datetime(
            datetime.combine(start_date, time(0, 0, 0))
        ).astimezone(timezone)
        
        end_ews = EWSDateTime.from_datetime(
            datetime.combine(end_date, time(23, 59, 59))
        ).astimezone(timezone)
        
        # Query calendar items
        calendar_items = account.calendar.view(
            start=start_ews,
            end=end_ews,
            max_items=1000
        )
        
        # Convert to list of dictionaries for easier processing
        events = []
        for item in calendar_items:
            if isinstance(item, CalendarItem):
                # Check if event should be considered as busy time
                # Include only events where user is organizer or has accepted
                should_include = False
                
                try:
                    # Check if user is organizer
                    if hasattr(item, 'is_from_me') and item.is_from_me:
                        should_include = True
                    # Check my_response_type for exchangelib
                    elif hasattr(item, 'my_response_type'):
                        # Include only if accepted
                        if str(item.my_response_type) in ['Accept', 'Organizer']:
                            should_include = True
                    # If no response info available, assume organizer
                    else:
                        should_include = True
                        
                    # Also check legacy_free_busy_status - exclude if marked as Free
                    if hasattr(item, 'legacy_free_busy_status'):
                        if str(item.legacy_free_busy_status) == 'Free':
                            should_include = False
                            
                except AttributeError:
                    # If we can't determine status, assume organizer
                    should_include = True
                
                if should_include:
                    events.append({
                        "subject": item.subject or "No Subject",
                        "start": item.start.astimezone(timezone).replace(tzinfo=None),
                        "end": item.end.astimezone(timezone).replace(tzinfo=None)
                    })
        
        return events
    except Exception as e:
        print(f"Error retrieving calendar events: {e}")
        sys.exit(1)


def find_free_slots(events, work_start_time, work_end_time, min_slot_duration=timedelta(minutes=45)):
    """
    Find free time slots between calendar events.
    
    Args:
        events: List of calendar events
        work_start_time: Work day start time
        work_end_time: Work day end time
        min_slot_duration: Minimum duration for a free slot to be considered
        
    Returns:
        list: List of free time slots
    """
    # Group events by date
    events_by_date = {}
    for event in events:
        date = event["start"].date()
        if date not in events_by_date:
            events_by_date[date] = []
        events_by_date[date].append(event)
    
    # Find free slots for each date
    free_slots = []
    for date, date_events in events_by_date.items():
        # Sort events by start time
        date_events.sort(key=lambda e: e["start"])
        
        # Set work day boundaries
        day_start = datetime.combine(date, work_start_time)
        day_end = datetime.combine(date, work_end_time)
        
        # Initialize current time to start of work day
        current_time = day_start
        
        # Process each event
        for event in date_events:
            event_start = event["start"]
            event_end = event["end"]
            
            # Skip events outside work hours
            if event_end <= day_start or event_start >= day_end:
                continue
            
            # Truncate events to work hours
            if event_start < day_start:
                event_start = day_start
            if event_end > day_end:
                event_end = day_end
            
            # If there's a gap between current time and event start, it's a free slot
            if event_start > current_time:
                slot_duration = event_start - current_time
                
                # Only consider slots longer than minimum duration
                if slot_duration >= min_slot_duration:
                    # Subtract minimum duration to get effective duration
                    effective_duration = slot_duration - min_slot_duration
                    
                    free_slots.append({
                        "date": date,
                        "start": current_time.time(),
                        "end": event_start.time(),
                        "duration": slot_duration,
                        "effective_duration": effective_duration
                    })
            
            # Move current time to end of this event
            if event_end > current_time:
                current_time = event_end
        
        # Check for free time between last event and end of work day
        if current_time < day_end:
            slot_duration = day_end - current_time
            
            # Only consider slots longer than minimum duration
            if slot_duration >= min_slot_duration:
                # Subtract minimum duration
                effective_duration = slot_duration - min_slot_duration
                
                free_slots.append({
                    "date": date,
                    "start": current_time.time(),
                    "end": day_end.time(),
                    "duration": slot_duration,
                    "effective_duration": effective_duration
                })
    
    return free_slots


def format_duration(duration):
    """Format timedelta as HH:MM."""
    total_minutes = int(duration.total_seconds() / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"


def analyze_calendar(app_dir, config):
    """
    Analyze calendar events and find free time slots.
    
    Args:
        app_dir: Path to application directory
        config: Configuration dictionary
    """
    # Validate configuration
    from calendar_tool.config import config as config_module
    if not config_module.validate_config(config):
        sys.exit(1)
    
    # Get authenticated account
    account = auth.get_authenticated_account(app_dir, config)
    if not account:
        sys.exit(1)
    
    # Parse work hours
    try:
        work_start_time = parse_time(config["start_time"])
        work_end_time = parse_time(config["end_time"])
    except ValueError:
        print("Error: Invalid time format in configuration.")
        sys.exit(1)
    
    # Calculate date range (past week)
    start_date = datetime.now().date()
    start_date += timedelta(days=-start_date.weekday(), weeks=-1)
    end_date = start_date + timedelta(days=4)
    
    print(f"Analyzing calendar from {start_date} to {end_date}...")
    print(f"Work hours: {config['start_time']} - {config['end_time']}")
    
    # Get calendar events
    events = get_calendar_events(account, start_date, end_date)
    
    if not events:
        print("No calendar events found for the specified period.")
        sys.exit(0)
    
    # Print events
    events_table = []
    for event in events:
        events_table.append([
            event["subject"],
            event["start"].date(),
            event["start"].time().strftime("%H:%M"),
            event["end"].time().strftime("%H:%M")
        ])
       
    # Group events by date for later calculation
    events_by_date = {}
    for event in events:
        date = event["start"].date()
        if date not in events_by_date:
            events_by_date[date] = []
        events_by_date[date].append(event)
        
    # Find free slots
    min_slot_duration = timedelta(minutes=45)
    free_slots = find_free_slots(events, work_start_time, work_end_time, min_slot_duration)
    
    # Print free slots
    print("\nFree Time Slots (>= 45 minutes):")
    if free_slots:
        slots_table = []
        total_duration = timedelta()
        total_effective_duration = timedelta()
        
        for slot in free_slots:
            slots_table.append([
                slot["date"],
                slot["start"].strftime("%H:%M"),
                slot["end"].strftime("%H:%M"),
                format_duration(slot["duration"])
            ])
            total_duration += slot["duration"]
            total_effective_duration += slot["effective_duration"]
        
        print(tabulate(slots_table, headers=["Date", "Start Time", "End Time", "Duration"], tablefmt="grid"))
        
        # Calculate work day duration
        work_day_duration = timedelta(hours=work_end_time.hour - work_start_time.hour,
                                     minutes=work_end_time.minute - work_start_time.minute)
        total_work_time = work_day_duration * len(events_by_date)
        
        # Print summary
        print("\nSummary:")
        print(f"Total free time: {format_duration(total_duration)}")
        print(f"Effective free time (after subtracting 45 min from each slot): {format_duration(total_effective_duration)}")
        print(f"Total work time: {format_duration(total_work_time)}")
        
        # Calculate percentage
        free_percentage = (total_effective_duration.total_seconds() / total_work_time.total_seconds()) * 100
        print(f"Free time percentage: {free_percentage:.2f}%")
    else:
        print("No free time slots found.")