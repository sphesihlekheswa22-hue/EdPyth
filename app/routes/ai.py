from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import json
import openai
from app import db
from app.models import (
    ChatSession, ChatMessage, StudyPlan, StudyPlanItem, 
    CourseMaterial, Course, Student, Enrollment, Quiz, QuizQuestion
)
from flask import current_app

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')


def get_ai_client():
    """Get NVIDIA AI client."""
    api_key = current_app.config.get('NVIDIA_API_KEY')
    if not api_key:
        return None
    return openai.OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )


@ai_bp.route('/chat')
@login_required
def chat():
    """AI Chat tutor main page."""
    if current_user.role != 'student':
        flash('AI tutoring is available for students only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get chat sessions
    sessions = ChatSession.query.filter_by(student_id=student.id)\
        .order_by(ChatSession.updated_at.desc()).limit(10).all()
    
    return render_template('ai_chat.html', sessions=sessions)


@ai_bp.route('/chat/new', methods=['POST'])
@login_required
def new_chat():
    """Start a new chat session."""
    if current_user.role != 'student':
        return jsonify({'error': 'Access denied'}), 403
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    course_id = request.form.get('course_id')
    topic = request.form.get('topic', 'General')
    
    session = ChatSession(
        student_id=student.id,
        course_id=course_id or None,
        topic=topic,
        title=f"Chat: {topic}"
    )
    
    db.session.add(session)
    db.session.commit()
    
    # Add welcome message
    welcome = ChatMessage(
        session_id=session.id,
        role='assistant',
        content=f"Hello! I'm your AI tutor. How can I help you with {topic} today?"
    )
    db.session.add(welcome)
    db.session.commit()
    
    return redirect(url_for('ai.chat_session', session_id=session.id))


@ai_bp.route('/chat/<int:session_id>')
@login_required
def chat_session(session_id):
    """View a specific chat session."""
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    session = ChatSession.query.get_or_404(session_id)
    if session.student_id != student.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('ai.chat'))
    
    messages = ChatMessage.query.filter_by(session_id=session_id)\
        .order_by(ChatMessage.created_at).all()
    
    # Get all sessions for sidebar
    sessions = ChatSession.query.filter_by(student_id=student.id)\
        .order_by(ChatSession.updated_at.desc()).limit(10).all()
    
    # Get enrolled courses for context
    enrollments = Enrollment.query.filter_by(student_id=student.id, status='active').all()
    courses = [e.course for e in enrollments]
    
    return render_template('ai_chat_session.html', session=session, 
                          messages=messages, sessions=sessions, courses=courses)


@ai_bp.route('/chat/<int:session_id>/send', methods=['POST'])
@login_required
def send_message(session_id):
    """Send a message to AI tutor."""
    if current_user.role != 'student':
        return jsonify({'error': 'Access denied'}), 403
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    session = ChatSession.query.get_or_404(session_id)
    if session.student_id != student.id:
        return jsonify({'error': 'Access denied'}), 403
    
    user_message = request.form.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    
    # Get conversation history
    messages = ChatMessage.query.filter_by(session_id=session_id)\
        .order_by(ChatMessage.created_at).all()
    
    # Build context
    context = f"You are an AI tutor for EduMind AI, a university Learning Management System. "
    
    if session.course:
        context += f"The student is currently studying {session.course.name}. "
    
    context += "Provide helpful, educational responses. Explain concepts clearly and provide examples when appropriate."
    
    # Prepare messages for OpenAI
    openai_messages = [{"role": "system", "content": context}]
    for msg in messages[-10:]:  # Last 10 messages for context
        openai_messages.append({"role": msg.role, "content": msg.content})
    openai_messages.append({"role": "user", "content": user_message})
    
    # Get AI response
    client = get_ai_client()
    if not client:
        # Fallback response if no API key
        ai_response = "I'm currently unavailable. Please configure your NVIDIA API key in the system settings."
    else:
        try:
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=openai_messages,
                max_tokens=500
            )
            ai_response = response.choices[0].message.content
        except Exception as e:
            ai_response = f"I apologize, but I encountered an error: {str(e)}. Please try again later."
    
    # Save AI response
    ai_msg = ChatMessage(
        session_id=session_id,
        role='assistant',
        content=ai_response
    )
    db.session.add(ai_msg)
    
    # Update session
    session.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return redirect(url_for('ai.chat_session', session_id=session_id))


@ai_bp.route('/summarize/<int:material_id>')
@login_required
def summarize_material(material_id):
    """Generate AI summary for a material."""
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    material = CourseMaterial.query.get_or_404(material_id)
    
    # Check enrollment
    student = Student.query.filter_by(user_id=current_user.id).first()
    enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=material.course_id).first()
    if not enrollment or enrollment.status != 'active':
        flash('Access denied.', 'danger')
        return redirect(url_for('courses.index'))
    
    # For now, return a placeholder (would need to read file content)
    flash('Summary feature requires file content extraction. This feature is under development.', 'info')
    return redirect(url_for('materials.list_materials', course_id=material.course_id))


@ai_bp.route('/study-plan/generate', methods=['POST'])
@login_required
def generate_study_plan():
    """Generate AI study plan."""
    if current_user.role != 'student':
        return jsonify({'error': 'Access denied'}), 403
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    course_id = request.form.get('course_id')
    duration_weeks = int(request.form.get('duration_weeks', 4))
    
    course = Course.query.get(course_id) if course_id else None
    
    # Get course context
    context = ""
    if course:
        context += f"Course: {course.name}\n"
        context += f"Description: {course.description or 'N/A'}\n"
        
        # Get modules
        modules = course.modules
        if modules:
            context += "Modules:\n"
            for m in modules:
                context += f"- {m.title}: {m.description or 'No description'}\n"
    
    # Create study plan
    plan = StudyPlan(
        student_id=student.id,
        course_id=course_id,
        title=f"Study Plan - {course.name if course else 'General'}",
        description="AI-generated personalized study plan",
        is_ai_generated=True,
        start_date=datetime.utcnow().date(),
        end_date=datetime.utcnow().date()
    )
    
    db.session.add(plan)
    db.session.commit()
    
    # Generate study plan items using AI or defaults
    client = get_ai_client()
    
    if client and context:
        try:
            prompt = f"""Create a {duration_weeks}-week study plan for the following course.
{context}

Provide a list of study tasks in this format:
Week 1:
- Task 1: [description]
- Task 2: [description]
Week 2:
...

Make it practical and focused on key topics."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            plan_content = response.choices[0].message.content
            
            # Parse and create items
            lines = plan_content.split('\n')
            week = 1
            order = 1
            for line in lines:
                if line.strip() and (line.startswith('-') or line[0].isdigit()):
                    item = StudyPlanItem(
                        study_plan_id=plan.id,
                        title=line.strip(),
                        task_type='general',
                        order=order,
                        priority='medium'
                    )
                    db.session.add(item)
                    order += 1
                    
                    if 'Week' in line:
                        week = int(''.join(filter(str.isdigit, line))) if any(c.isdigit() for c in line) else week
        except Exception as e:
            # Fallback to default items
            pass
    
    # If no items created, add defaults
    if not plan.items:
        default_items = [
            "Review course syllabus and objectives",
            "Complete reading assignments",
            "Practice with exercises",
            "Review and summarize notes",
            "Take practice quizzes"
        ]
        
        for i, title in enumerate(default_items):
            item = StudyPlanItem(
                study_plan_id=plan.id,
                title=title,
                task_type='general',
                order=i+1,
                priority='medium'
            )
            db.session.add(item)
    
    db.session.commit()
    
    flash('Study plan generated!', 'success')
    return redirect(url_for('ai.view_study_plan', plan_id=plan.id))


@ai_bp.route('/study-plan/<int:plan_id>')
@login_required
def view_study_plan(plan_id):
    """View a study plan."""
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    plan = StudyPlan.query.get_or_404(plan_id)
    if plan.student_id != student.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    items = StudyPlanItem.query.filter_by(study_plan_id=plan_id)\
        .order_by(StudyPlanItem.order).all()
    
    return render_template('study_plan.html', plan=plan, items=items)


@ai_bp.route('/study-plan/<int:item_id>/complete', methods=['POST'])
@login_required
def complete_study_item(item_id):
    """Mark a study plan item as complete."""
    if current_user.role != 'student':
        return jsonify({'error': 'Access denied'}), 403
    
    item = StudyPlanItem.query.get_or_404(item_id)
    plan = item.study_plan
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if plan.student_id != student.id:
        return jsonify({'error': 'Access denied'}), 403
    
    item.status = 'completed'
    item.completed_at = datetime.utcnow()
    db.session.commit()
    
    flash('Item marked as complete!', 'success')
    return redirect(url_for('ai.view_study_plan', plan_id=plan.id))
