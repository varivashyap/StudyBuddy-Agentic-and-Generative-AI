"""
Google Calendar API integration for MCP Server.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials


class GoogleCalendarService:
    """Service for interacting with Google Calendar API."""
    
    def __init__(self, credentials: Credentials):
        """
        Initialize Google Calendar Service.
        
        Args:
            credentials: Google OAuth credentials
        """
        self.credentials = credentials
        self.service = build('calendar', 'v3', credentials=credentials)
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all calendars for the authenticated user.
        
        Returns:
            List of calendar dictionaries
        """
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            return [
                {
                    'id': cal.get('id'),
                    'summary': cal.get('summary'),
                    'description': cal.get('description'),
                    'primary': cal.get('primary', False),
                    'accessRole': cal.get('accessRole'),
                    'backgroundColor': cal.get('backgroundColor'),
                    'foregroundColor': cal.get('foregroundColor')
                }
                for cal in calendars
            ]
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
    
    def get_events(self, 
                   time_min: Optional[str] = None,
                   time_max: Optional[str] = None,
                   calendar_id: str = 'primary',
                   max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Get calendar events within a time range.
        
        Args:
            time_min: Start time (ISO format)
            time_max: End time (ISO format)
            calendar_id: Calendar ID (default: 'primary')
            max_results: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        try:
            # Default to next 30 days if not specified
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            if not time_max:
                time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return [
                {
                    'id': event.get('id'),
                    'summary': event.get('summary', 'Untitled'),
                    'title': event.get('summary', 'Untitled'),  # Keep both for compatibility
                    'description': event.get('description'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'allDay': 'date' in event['start'],
                    'location': event.get('location'),
                    'calendarId': calendar_id
                }
                for event in events
            ]
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
    
    def create_event(self, event_data: Dict[str, Any], calendar_id: str = 'primary') -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            event_data: Event data dictionary
            calendar_id: Calendar ID (default: 'primary')
            
        Returns:
            Created event dictionary
        """
        try:
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()
            
            return {
                'id': event.get('id'),
                'title': event.get('summary'),
                'description': event.get('description'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'location': event.get('location'),
                'htmlLink': event.get('htmlLink')
            }
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
    
    def update_event(self, event_id: str, event_data: Dict[str, Any], 
                    calendar_id: str = 'primary') -> Dict[str, Any]:
        """
        Update an existing calendar event.
        
        Args:
            event_id: Event ID
            event_data: Updated event data
            calendar_id: Calendar ID (default: 'primary')
            
        Returns:
            Updated event dictionary
        """
        try:
            event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event_data
            ).execute()
            
            return {
                'id': event.get('id'),
                'title': event.get('summary'),
                'description': event.get('description'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'location': event.get('location')
            }
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise

    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: Event ID
            calendar_id: Calendar ID (default: 'primary')

        Returns:
            True if successful
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise

