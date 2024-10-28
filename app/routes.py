import io
import json
from datetime import datetime

from Bio.Blast import NCBIWWW
from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app import app, db
from app.models import User, Task
from app.utils import parse_blast_results


@app.route('/')
def main_index():
    return render_template('main_index.html')


@app.route('/<username>')
@login_required
def user_index(username):
    if username != current_user.username:
        flash('无权访问该用户的主页！', 'danger')
        return redirect(url_for('user_index', username=current_user.username))
    user = User.query.filter_by(username=username).first_or_404()
    tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template('user_index.html', tasks=tasks, user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return render_template('register.html', username_taken=True)
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('user_index', username=user.username))
        else:
            return render_template('login.html', error=True)
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main_index'))


@app.route('/blast', methods=['GET', 'POST'])
@login_required
def blast():
    task_running = False
    if request.method == 'POST':
        task_running = True
        data = request.form
        program = data.get('program')
        database = data.get('database')
        sequence = data.get('sequence')
        try:
            result_handle = NCBIWWW.qblast(program, database, sequence)
            blast_results = result_handle.read()
            result_handle.close()
            parsed_results = parse_blast_results(io.StringIO(blast_results))
            formatted_taskname = f"{program}_{database}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            task = Task(
                taskname=formatted_taskname,
                program=program,
                database=database,
                sequence=sequence,
                result=json.dumps(parsed_results),
                user_id=current_user.id
            )
            db.session.add(task)
            db.session.commit()
            flash('BLAST成功!', 'success')
            return redirect(url_for('user_index', username=current_user.username))
        except Exception as e:
            flash(f"发生错误: {str(e)}", 'danger')
            return render_template('blast.html', task_running=task_running)
    return render_template('blast.html', task_running=task_running)


@app.route('/<username>/<taskname>', methods=['GET'])
@login_required
def results(username, taskname):
    user = User.query.filter_by(username=username).first_or_404()
    task = Task.query.filter_by(taskname=taskname, user_id=user.id).first_or_404()
    if task.user_id != current_user.id:
        flash('无权访问该任务的结果！', 'danger')
        return redirect(url_for('user_index', username=current_user.username))
    parsed_results = json.loads(task.result) if task.result else []
    return render_template('results.html', task=task, results=parsed_results)


@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        flash('任务已成功删除！', 'success')
    else:
        flash('无权删除该任务或任务不存在！', 'error')
    return redirect(url_for('user_index', username=current_user.username))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(Exception)
def handle_exception(error):
    response = jsonify({"error": str(error)})
    response.status_code = 500
    return response
