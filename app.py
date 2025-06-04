from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'
if os.getenv("DATABASE_URL"):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
else:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agendamentos.db'
db = SQLAlchemy(app)


class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professor = db.Column(db.String(100), nullable=False)
    turno = db.Column(db.String(20), nullable=False)
    gabinete = db.Column(db.Integer, nullable=False)
    data = db.Column(db.String(10), nullable=False)


with app.app_context():
    db.create_all()


@app.template_filter('format_date')
def format_date(value):
    return datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/book', methods=['POST'])
def book():
    professor = request.form['professor']
    turno = request.form['turno']
    gabinete = int(request.form['gabinete'])
    data = request.form['data']

    data_obj = datetime.strptime(data, '%Y-%m-%d')
    if data_obj.date() < datetime.now().date():
        flash('Não é possível agendar para datas passadas.')
        return redirect(url_for('index'))

    conflito = Agendamento.query.filter_by(data=data, turno=turno, gabinete=gabinete).first()
    if conflito:
        flash(f'Gabinete {gabinete} já está reservado no turno {turno} para {data}.')
        return redirect(url_for('index'))

    agendamento = Agendamento(professor=professor, turno=turno, gabinete=gabinete, data=data)
    db.session.add(agendamento)
    db.session.commit()

    flash('Reserva efetuada com sucesso!')
    return redirect(url_for('index'))


@app.route('/schedule')
def view_schedule():
    agendamentos = Agendamento.query.order_by(Agendamento.data.desc()).all()
    return render_template('schedule.html', agendamentos=agendamentos)


@app.route('/delete/<int:id>')
def delete(id):
    agendamento = Agendamento.query.get_or_404(id)
    db.session.delete(agendamento)
    db.session.commit()
    flash('Reserva cancelada com sucesso!')
    return redirect(url_for('view_schedule'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    agendamento = Agendamento.query.get_or_404(id)
    if request.method == 'POST':
        agendamento.professor = request.form['professor']
        agendamento.turno = request.form['turno']
        agendamento.gabinete = int(request.form['gabinete'])
        agendamento.data = request.form['data']

        conflito = Agendamento.query.filter(
            Agendamento.id != id,
            Agendamento.data == agendamento.data,
            Agendamento.turno == agendamento.turno,
            Agendamento.gabinete == agendamento.gabinete
        ).first()

        if conflito:
            flash('Já existe um agendamento nesse horário para esse gabinete.')
            return redirect(url_for('edit', id=id))

        db.session.commit()
        flash('Reserva atualizada com sucesso!')
        return redirect(url_for('view_schedule'))

    return render_template('edit.html', agendamento=agendamento)


if __name__ == '__main__':
    app.run(debug=True)
