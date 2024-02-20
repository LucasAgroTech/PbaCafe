from flask import Flask, render_template, redirect, url_for, request
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
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
    nome_desafio = db.Column(db.String(120), nullable=False)
    responsavel = db.Column(db.String(120), nullable=False)
    email_usuario = db.Column(db.String(255), nullable=False)
    departamento = db.Column(db.String(50), nullable=False)
    area = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    resultado_esperado = db.Column(db.Text, nullable=False)
    necessidade = db.Column(db.Text, nullable=False)
    tipo_desafio = db.Column(db.Text, nullable=False)
    explicacao = db.Column(db.Text, nullable=False)
    valor_agregado = db.Column(db.Text, nullable=False)
    recursos = db.Column(db.Text, nullable=False)
    tentativas = db.Column(db.String(120), nullable=True)
    link_materiais = db.Column(db.String(120), nullable=True)
    anexo_url = db.Column(db.String(255), nullable=True)
    aceite_termos = db.Column(db.Boolean, default=False, nullable=False)


def create_tables():
    with app.app_context():
        db.create_all()


create_tables()


@app.route("/inscricao", methods=["POST"])
def add_inscricao():
    nome_desafio = request.form["nome_desafio"]
    responsavel = request.form["responsavel"]
    email_usuario = request.form["email_usuario"]
    departamento = request.form["departamento"]
    area = request.form["area"]
    descricao = request.form["descricao"]
    resultado_esperado = request.form["resultado_esperado"]
    necessidade = request.form["necessidade"]
    tipo_desafio = request.form.getlist("tipo_desafio[]")
    explicacao = request.form["explicacao"]
    valor_agregado = request.form["valor_agregado"]
    recursos = request.form["recursos"]
    tentativas = request.form.get("tentativas", "")
    link_materiais = request.form.get("link_materiais", "")
    aceite_termos = request.form.get("aceite_termos") == "on"

    nova_inscricao = Inscricao(
        nome_desafio=nome_desafio,
        responsavel=responsavel,
        email_usuario=email_usuario,
        departamento=departamento,
        area=area,
        descricao=descricao,
        resultado_esperado=resultado_esperado,
        necessidade=necessidade,
        tipo_desafio=",".join(tipo_desafio),
        explicacao=explicacao,
        valor_agregado=valor_agregado,
        recursos=recursos,
        tentativas=tentativas,
        link_materiais=link_materiais,
        aceite_termos=aceite_termos,
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
    inscricoes = Inscricao.query.all()  # Busca todas as inscrições no banco de dados
    return render_template("listar_inscricoes.html", inscricoes=inscricoes)


if __name__ == "__main__":
    app.run(debug=True)
