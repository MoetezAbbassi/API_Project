"""
Calendar Routes - Manage fitness calendar events
Endpoints: 3 (GET month-view, POST create-event, DELETE event)
"""
from flask import Blueprint, request
from datetime import datetime
from app.extensions import db

from app.models import CalendarEvent, Workout, User
from app.utils import validators, responses, decorators

bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')


def serialize_calendar_event(event: CalendarEvent) -> dict:
    """
    Serialize CalendarEvent object to dictionary
    
    Args:
        event: CalendarEvent model instance
        
    Returns:
        Dictionary representation of calendar event
    """
    return {
        "event_id": event.event_id,
        "event_date": event.event_date.isoformat() if event.event_date else None,
        "event_type": event.event_type,
        "event_title": event.event_title,
        "related_id": event.related_id,
        "event_details": event.event_details,
        "created_at": event.created_at.isoformat() if event.created_at else None
    }


@bp.route('/<user_id>', methods=['GET'])
@decorators.token_required
def get_calendar(token_user_id, user_id):
    """
    Get calendar view for user with events for a month
    
    Query params:
    - month: Month filter (YYYY-MM format)
    - type: Event type filter (workout, rest, meal, goal, other)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'), type=str)
        event_type = request.args.get('type', type=str)
        
        # Parse month
        try:
            month_date = datetime.strptime(month_str, '%Y-%m')
        except ValueError:
            return responses.validation_error_response("Invalid month format. Use YYYY-MM")
        
        # Get all events for month
        query = db.session.query(CalendarEvent).filter_by(user_id=user_id)
        
        # Filter by month
        start_date = month_date.replace(day=1)
        if month_date.month == 12:
            end_date = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            end_date = month_date.replace(month=month_date.month + 1, day=1)
        
        query = query.filter(CalendarEvent.event_date >= start_date.date(), CalendarEvent.event_date < end_date.date())
        
        # Filter by type if provided
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        events = query.order_by(CalendarEvent.event_date).all()
        
        # Calculate statistics
        total_events = len(events)
        workout_days = len([e for e in events if e.event_type == 'workout'])
        rest_days = len([e for e in events if e.event_type == 'rest'])
        
        response_data = {
            "month": month_str,
            "events": [serialize_calendar_event(e) for e in events],
            "total_events": total_events,
            "workout_days": workout_days,
            "rest_days": rest_days
        }
        
        return responses.success_response(
            response_data,
            "Calendar retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "CALENDAR_GET_ERROR",
            500
        )


@bp.route('/events', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def create_calendar_event(token_user_id):
    """
    Create calendar event
    
    Request body:
    {
        "event_date": "2026-01-11",
        "event_type": "workout|rest|meal|goal|other",
        "event_title": "Upper Body Workout",
        "related_id": "workout_uuid_or_null",
        "event_details": {"notes": "optional"}
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(
            data, ['event_date', 'event_type', 'event_title']
        )
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate date
        is_valid, error_msg = validators.validate_date(data['event_date'])
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate event type
        valid_types = ['workout', 'rest', 'meal', 'goal', 'other']
        is_valid, error_msg = validators.validate_enum(data['event_type'], valid_types)
        if not is_valid:
            return responses.validation_error_response(f"Invalid event_type. Must be one of: {', '.join(valid_types)}")
        
        # Parse date
        event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
        
        # Create event
        import uuid
        import json
        event = CalendarEvent(
            event_id=str(uuid.uuid4()),
            user_id=token_user_id,
            event_date=event_date,
            event_type=data['event_type'],
            event_title=data['event_title'],
            related_id=data.get('related_id'),
            event_details=json.dumps(data.get('event_details', {}))
        )
        
        db.session.add(event)
        db.session.commit()
        
        return responses.created_response(
            serialize_calendar_event(event),
            "Calendar event created successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "CALENDAR_EVENT_CREATE_ERROR",
            500
        )


@bp.route('/events/<event_id>', methods=['DELETE'])
@decorators.token_required
def delete_calendar_event(token_user_id, event_id):
    """
    Delete calendar event
    
    Path params:
    - event_id: Event ID (UUID)
    """
    try:
        # Verify event exists
        event = db.session.query(CalendarEvent).filter_by(event_id=event_id).first()
        if not event:
            return responses.not_found_response("Calendar event not found")
        
        # Security: verify user owns event
        if event.user_id != token_user_id:
            return responses.forbidden_response("You can only delete your own calendar events")
        
        db.session.delete(event)
        db.session.commit()
        
        return responses.deleted_response("Calendar event deleted successfully")
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "CALENDAR_EVENT_DELETE_ERROR",
            500
        )
