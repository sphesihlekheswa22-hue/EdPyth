from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Notification, Student, Lecturer, InterventionMessage
from app.utils.app_time import app_timestamp
from app.services.notification_service import NotificationService
from app import csrf

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def index():
    """Render notifications page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    pagination = NotificationService.get_notifications(
        current_user, 
        page=page, 
        per_page=per_page,
        unread_only=False
    )
    
    return render_template(
        'notifications.html',
        notifications=pagination.items,
        pagination=pagination
    )


@notifications_bp.route('/api/notifications')
@login_required
def api_get_notifications():
    """Get notifications for current user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    
    pagination = NotificationService.get_notifications(
        current_user,
        page=page,
        per_page=per_page,
        unread_only=unread_only
    )
    
    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'unread_count': NotificationService.get_unread_count(current_user)
    })


@notifications_bp.route('/api/notifications/unread-count')
@login_required
def api_unread_count():
    """Get just the unread count (for navbar badge)"""
    return jsonify({
        'count': NotificationService.get_unread_count(current_user),
        'last_read': current_user.last_notification_read.isoformat() if current_user.last_notification_read else None
    })


@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def api_mark_as_read(notification_id):
    """Mark single notification as read"""
    notif = Notification.query.filter_by(
        id=notification_id, 
        recipient_id=current_user.id
    ).first_or_404()
    
    notif.mark_as_read()
    return jsonify({
        'success': True, 
        'unread_count': NotificationService.get_unread_count(current_user)
    })


@notifications_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_read():
    """Mark all as read"""
    NotificationService.mark_all_as_read(current_user)
    return jsonify({'success': True, 'count': 0})


@notifications_bp.route('/api/notifications/poll')
@login_required
def api_poll_notifications():
    """
    Long-polling endpoint for real-time updates
    Returns immediately if new notifications exist
    """
    since = request.args.get('since', type=float)
    
    query = Notification.query.filter_by(recipient_id=current_user.id)
    
    if since:
        since_dt = datetime.fromtimestamp(since)
        query = query.filter(Notification.created_at > since_dt)
    
    new_notifications = query.order_by(Notification.created_at.asc()).all()
    
    return jsonify({
        'notifications': [n.to_dict() for n in new_notifications],
        'timestamp': app_timestamp(),
        'has_new': len(new_notifications) > 0
    })


# Intervention routes
@notifications_bp.route('/interventions/sent')
@login_required
def interventions_sent():
    """Render page showing sent interventions (for lecturers)"""
    if current_user.role != 'lecturer':
        return jsonify({'error': 'Only lecturers can view this'}), 403
    
    lecturer = Lecturer.query.filter_by(user_id=current_user.id).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    pagination = NotificationService.get_interventions_sent(lecturer, page=page)
    
    return render_template(
        'interventions_sent.html',
        interventions=pagination.items,
        pagination=pagination
    )


@notifications_bp.route('/interventions/received')
@login_required
def interventions_received():
    """Render page showing received interventions (for students)"""
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can view this'}), 403
    
    student = Student.query.filter_by(user_id=current_user.id).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    pagination = NotificationService.get_interventions_received(student, page=page)
    
    return render_template(
        'interventions_received.html',
        interventions=pagination.items,
        pagination=pagination
    )


@notifications_bp.route('/intervention/<int:intervention_id>')
@login_required
def intervention_detail(intervention_id):
    """View single intervention detail"""
    intervention = InterventionMessage.query.get_or_404(intervention_id)
    
    # Check access
    if current_user.role == 'student':
        if intervention.student.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        # Mark as opened
        student = Student.query.filter_by(user_id=current_user.id).first()
        NotificationService.mark_intervention_opened(intervention_id, student.id)
    elif current_user.role == 'lecturer':
        if intervention.lecturer.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    else:
        return jsonify({'error': 'Access denied'}), 403
    
    return render_template(
        'intervention_detail.html',
        intervention=intervention
    )


@notifications_bp.route('/api/interventions/send', methods=['POST'])
@login_required
@csrf.exempt
def api_send_intervention():
    """Send intervention message from lecturer to student"""
    if current_user.role != 'lecturer':
        return jsonify({'error': 'Only lecturers can send interventions'}), 403
    
    data = request.get_json()
    student_id = data.get('student_id')
    message = data.get('message')
    template = data.get('template', 'custom')
    course_id = data.get('course_id')
    
    if not student_id or not message:
        return jsonify({'error': 'Student ID and message required'}), 400
    
    # Get lecturer record
    lecturer = Lecturer.query.filter_by(user_id=current_user.id).first_or_404()
    student = Student.query.get_or_404(student_id)
    course = None
    if course_id:
        from app.models import Course
        course = Course.query.get(course_id)
    
    try:
        intervention, notification = NotificationService.notify_student_intervention(
            lecturer=lecturer,
            student=student,
            course=course,
            message_content=message,
            template=template
        )
        
        return jsonify({
            'success': True,
            'intervention_id': intervention.id,
            'notification_id': notification.id,
            'message': 'Intervention sent successfully'
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/interventions/<int:intervention_id>/reply', methods=['POST'])
@login_required
@csrf.exempt
def api_reply_intervention(intervention_id):
    """Student replies to an intervention"""
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can reply to interventions'}), 403
    
    data = request.get_json()
    reply_content = data.get('message')
    
    if not reply_content:
        return jsonify({'error': 'Message required'}), 400
    
    student = Student.query.filter_by(user_id=current_user.id).first_or_404()
    
    try:
        intervention, notification = NotificationService.reply_to_intervention(
            intervention_id=intervention_id,
            student_id=student.id,
            reply_content=reply_content
        )
        
        if not intervention:
            return jsonify({'error': 'Intervention not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Reply sent successfully'
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
