from flask import Flask, render_template, redirect, url_for, request
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import cloudinary.uploader
import cloudinary
import os

app = Flask(__name__)
uri = os.getenv(
    "DATABASE_URL"
)  # Obter a URI do banco de dados a partir das variáveis de ambiente
if uri and uri.startswith("postgres://"):
    uri = uri.replace(
        "postgres://", "postgresql://", 1
    )  # Substituir apenas a primeira ocorrência
app.config["SQLALCHEMY_DATABASE_URI"] = uri
db = SQLAlchemy(app)

cloudinary.config(
    cloud_name="hbmghdcte",
    api_key="728847166383671",
    api_secret="PJPwG2x4O2GnsgxVmjfQg8ppJx4",
)


class Inscricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_desafio = db.Column(db.String(120), nullable=False)
    responsavel = db.Column(db.String(120), nullable=False)
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
    anexo_url = db.Column(db.String(255), nullable=True)  # Mova esta linha para aqui


def create_tables():
    with app.app_context():
        db.create_all()


create_tables()


@app.route("/inscricao", methods=["POST"])
def add_inscricao():
    # Captura os dados do formulário
    nome_desafio = request.form["nome_desafio"]
    responsavel = request.form["responsavel"]
    departamento = request.form["departamento"]
    area = request.form["area"]
    descricao = request.form["descricao"]
    resultado_esperado = request.form["resultado_esperado"]
    necessidade = request.form["necessidade"]
    tipo_desafio = request.form.getlist("tipo_desafio[]")
    explicacao = request.form["explicacao"]
    valor_agregado = request.form["valor_agregado"]
    recursos = request.form["recursos"]
    tentativas = request.form.get("tentativas")
    link_materiais = request.form.get("link_materiais")
    anexo_url = db.Column(db.String(255), nullable=True)

    # Cria uma nova instância do modelo Inscricao
    nova_inscricao = Inscricao(
        nome_desafio=nome_desafio,
        responsavel=responsavel,
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
    )

    # Verifica se há um arquivo no formulário
    file_to_upload = request.files.get("anexar_documentos")
    if file_to_upload and file_to_upload.filename != "":
        filename = secure_filename(file_to_upload.filename)
        upload_result = cloudinary.uploader.upload(file_to_upload)
        anexo_url = upload_result["url"]
        nova_inscricao.anexo_url = (
            anexo_url  # Certifique-se de que esta linha está correta
        )

    db.session.add(nova_inscricao)
    db.session.commit()

    return redirect(url_for("index"))


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
