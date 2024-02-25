from flask import Flask, render_template, redirect, url_for, request, send_file, jsonify
from flask_mail import Mail, Message
from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import io
import pyexcel as p
import cloudinary.uploader
import cloudinary
import os

app = Flask(__name__)
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
db = SQLAlchemy(app)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# Configurações do Flask-Mail
app.config["MAIL_SERVER"] = "smtp.hostinger.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
mail = Mail(app)


class Inscricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    responsavel = db.Column(db.String(120), nullable=False)
    email_usuario = db.Column(db.String(255), nullable=False)
    departamento = db.Column(db.String(120), nullable=False)
    area = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    resultado_esperado = db.Column(db.Text, nullable=False)
    explicacao = db.Column(db.Text, nullable=False)
    link_materiais = db.Column(db.String(255), nullable=True)
    anexo_url = db.Column(db.String(255), nullable=True)
    informacoes = db.Column(db.Text, nullable=True)
    aceite_termos = db.Column(db.Boolean, default=False, nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "data_hora": self.data_hora.strftime("%Y-%m-%d %H:%M:%S"),
            "responsavel": self.responsavel,
            "email_usuario": self.email_usuario,
            "departamento": self.departamento,
            "area": self.area,
            "descricao": self.descricao,
            "resultado_esperado": self.resultado_esperado,
            "explicacao": self.explicacao,
            "informacoes": self.informacoes,
            "link_materiais": self.link_materiais,
            "anexo_url": self.anexo_url,
            "aceite_termos": self.aceite_termos,
        }


@app.route("/ficha/<int:inscricao_id>")
def ficha_inscricao(inscricao_id):
    inscricao = Inscricao.query.get_or_404(inscricao_id)
    return render_template("ficha_inscricao.html", inscricao=inscricao)


def create_tables():
    with app.app_context():
        db.create_all()


@app.route("/inscricao", methods=["POST"])
def add_inscricao():
    responsavel = request.form["responsavel"]
    email_usuario = request.form["email_usuario"]
    departamento = request.form["departamento"]
    area = request.form["area"]
    descricao = request.form["descricao"]
    resultado_esperado = request.form["resultado_esperado"]
    explicacao = request.form["explicacao"]
    link_materiais = request.form.get("link_materiais", "")
    informacoes = request.form.get("informacoes", "")
    aceite_termos = request.form.get("aceite_termos") == "on"

    nova_inscricao = Inscricao(
        responsavel=responsavel,
        email_usuario=email_usuario,
        departamento=departamento,
        area=area,
        descricao=descricao,
        resultado_esperado=resultado_esperado,
        explicacao=explicacao,
        link_materiais=link_materiais,
        informacoes=informacoes,
        aceite_termos=aceite_termos,
        data_hora=datetime.utcnow(),
    )

    file_to_upload = request.files.get("anexar_documentos")
    if file_to_upload and file_to_upload.filename != "":
        upload_result = cloudinary.uploader.upload(file_to_upload)
        anexo_url = upload_result["url"]
        nova_inscricao.anexo_url = anexo_url

    db.session.add(nova_inscricao)
    db.session.commit()

    # Preparando o conteúdo do e-mail utilizando um template HTML
    to_email = email_usuario  # Usa o e-mail fornecido pelo usuário
    subject = "Confirmação de Inscrição"

    # Renderiza o template HTML como string, passando a variável 'responsavel' como 'nome_produtor'
    html_content = render_template("email_template.html", nome_produtor=responsavel)

    # Dispara o e-mail após salvar a inscrição
    send_email(to_email, subject, html_content)

    return redirect(url_for("index", success=True))


def send_email(to_email, subject, html_content):
    with app.app_context():
        msg = Message(subject, recipients=[to_email], html=html_content)
        mail.send(msg)


@app.route("/", methods=["GET"])
def index():
    return render_template("formulario.html")


@app.route("/formulario", methods=["GET"])
def formulario():
    return render_template("formulario.html")


@app.route("/inscricoes", methods=["GET"])
def listar_inscricoes():
    inscricoes = Inscricao.query.all()
    return render_template("listar_inscricoes.html", inscricoes=inscricoes)


# Rota para baixar os dados em Excel
@app.route("/download_excel", methods=["GET"])
def download_excel():
    query_sets = Inscricao.query.all()
    data = [inscricao.to_dict() for inscricao in query_sets]

    output = io.BytesIO()
    sheet = p.get_sheet(records=data)
    sheet.save_to_memory("xlsx", output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="Inscricoes.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    app.run(debug=True)
