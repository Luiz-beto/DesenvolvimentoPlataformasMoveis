# app.py
import os
from io import BytesIO
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_file, abort, flash, session
)
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB

DB = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "loja_grid"),
    "cursorclass": DictCursor,
    "charset": "utf8mb4",
    "autocommit": True,
}

def db():
    return pymysql.connect(**DB)

# ------------------ Helpers de Flash ------------------
def flash_ok(msg: str):
    flash(msg, "ok")

def flash_err(msg: str):
    flash(msg, "err")

def flash_info(msg: str):
    flash(msg, "info")

def flash_warn(msg: str):
    flash(msg, "warn")

# ------------------ Auth helpers ------------------
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, nome_usuario, papel FROM usuarios WHERE id=%s", (uid,))
        return cur.fetchone()

def login_required(fn):
    @wraps(fn)
    def _wrap(*args, **kwargs):
        if not session.get("uid"):
            flash_warn("Faça login para continuar.")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return _wrap

def admin_required(fn):
    @wraps(fn)
    def _wrap(*args, **kwargs):
        u = current_user()
        if not u or u["papel"] != "admin":
            flash_err("Acesso restrito a administradores.")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)
    return _wrap

def is_image(file_storage):
    return bool(file_storage and (file_storage.mimetype or "").lower().startswith("image/"))

# ------------------ Contexto global (user + banners) ------------------
@app.context_processor
def inject_globals():
    u = current_user()

    banners = []
    banner = None
    banner_url = None
    try:
        with db() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, UNIX_TIMESTAMP(criado_em) AS v FROM banners ORDER BY id DESC")
            rows = cur.fetchall() or []
            for r in rows:
                r["url"] = url_for("banner_imagem", id=r["id"]) + f"?v={r.get('v') or 0}"
                banners.append(r)
            if rows:
                banner = rows[0]
                banner_url = banner["url"]
    except Exception:
        # Evita quebrar layout caso DB falhe só aqui
        pass

    return {
        "user": u,
        "current_user": u,   # alias
        "banners": banners,
        "banner": banner,
        "banner_url": banner_url,
        "current_year": datetime.utcnow().year,  # útil pra footer/páginas
    }

# ------------------ Páginas ------------------
@app.route("/sobre")
def about():
    return render_template("about.html")

@app.route("/about")
def about_alias():
    return redirect(url_for("about"))

@app.route("/contact")
def contact():
    return redirect(url_for("contatos_page"))

@app.route("/")
def index():
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, nome, descricao, preco, UNIX_TIMESTAMP(criado_em) AS v "
            "FROM produtos ORDER BY id DESC LIMIT 100"
        )
        produtos = cur.fetchall()

    for p in produtos:
        p["imagem_url"] = url_for("produto_imagem", id=p["id"]) + f"?v={p.get('v') or 0}"

    return render_template("index.html", produtos=produtos)

# ------------------ Auth ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        with db() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, nome_usuario, senha_hash, papel FROM usuarios WHERE nome_usuario=%s", (username,))
            u = cur.fetchone()
        if u and check_password_hash(u["senha_hash"], password):
            session["uid"] = u["id"]
            flash_ok("Login efetuado com sucesso.")
            return redirect(request.args.get("next") or url_for("index"))
        flash_err("Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash_info("Sessão encerrada.")
    return redirect(url_for("login"))

# ------------------ Produtos ------------------
@app.route("/produtos", methods=["POST"])
@admin_required
def criar_produto():
    nome = (request.form.get("nome") or "").strip()
    preco = request.form.get("preco")
    descricao = (request.form.get("descricao") or None)
    file = request.files.get("imagem")

    if not nome:
        flash_err("Informe o nome do produto.")
        return redirect(request.referrer or url_for("index"))

    try:
        preco_val = float(preco) if preco not in (None, "") else 0.0
    except ValueError:
        flash_err("Preço inválido.")
        return redirect(request.referrer or url_for("index"))

    img_bytes = img_name = img_mime = None
    img_size = None
    if file and file.filename:
        if not is_image(file):
            flash_err("Arquivo de imagem inválido.")
            return redirect(request.referrer or url_for("index"))
        data = file.read()
        img_bytes, img_name, img_mime, img_size = data, file.filename, file.mimetype, len(data)

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO produtos (nome, descricao, preco, imagem, imagem_nome, imagem_mime, imagem_tamanho)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (nome, descricao, preco_val, img_bytes, img_name, img_mime, img_size),
        )
    flash_ok("Produto adicionado!")
    return redirect(request.referrer or url_for("index"))

@app.route("/produtos/<int:id>", methods=["POST"])
@admin_required
def editar_produto(id:int):
    nome = (request.form.get("nome") or "").strip()
    preco = request.form.get("preco")
    descricao = (request.form.get("descricao") or None)
    file = request.files.get("imagem")

    if not nome:
        flash_err("Nome é obrigatório.")
        return redirect(request.referrer or url_for("index"))
    try:
        preco_val = float(preco) if preco not in (None, "") else 0.0
    except ValueError:
        flash_err("Preço inválido.")
        return redirect(request.referrer or url_for("index"))

    with db() as conn, conn.cursor() as cur:
        if file and file.filename:
            if not is_image(file):
                flash_err("Imagem inválida.")
                return redirect(request.referrer or url_for("index"))
            data = file.read()
            cur.execute(
                """UPDATE produtos SET nome=%s, descricao=%s, preco=%s,
                   imagem=%s, imagem_nome=%s, imagem_mime=%s, imagem_tamanho=%s
                   WHERE id=%s""",
                (nome, descricao, preco_val, data, file.filename, file.mimetype, len(data), id),
            )
        else:
            cur.execute(
                "UPDATE produtos SET nome=%s, descricao=%s, preco=%s WHERE id=%s",
                (nome, descricao, preco_val, id),
            )
    flash_ok("Produto atualizado.")
    return redirect(request.referrer or url_for("index"))

@app.route("/produtos/<int:id>/delete", methods=["POST"])
@admin_required
def excluir_produto(id:int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM produtos WHERE id=%s", (id,))
    flash_info("Produto excluído.")
    return redirect(request.referrer or url_for("index"))

@app.route("/produtos/<int:id>/imagem")
def produto_imagem(id:int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT imagem, imagem_mime FROM produtos WHERE id=%s", (id,))
        row = cur.fetchone()
        if not row or not row["imagem"]:
            # 1x1 gif transparente
            return send_file(BytesIO(
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
                b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"),
                mimetype="image/gif")
        return send_file(BytesIO(row["imagem"]),
                         mimetype=row.get("imagem_mime") or "application/octet-stream",
                         as_attachment=False, download_name=f"produto_{id}", max_age=3600, conditional=True)

# ------------------ Banner ------------------
@app.route("/admin/banner", methods=["POST"])
@admin_required
def salvar_banner():
    file = request.files.get("imagem")
    if not (file and file.filename and is_image(file)):
        flash_err("Envie uma imagem válida para o banner.")
        return redirect(request.referrer or url_for("index"))
    data = file.read()
    with db() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO banners (imagem, imagem_nome, imagem_mime) VALUES (%s,%s,%s)",
                    (data, file.filename, file.mimetype))
    flash_ok("Banner salvo.")
    return redirect(request.referrer or url_for("index"))

@app.route("/admin/banner/<int:id>/delete", methods=["POST"])
@admin_required
def excluir_banner(id:int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM banners WHERE id=%s", (id,))
    flash_info("Banner excluído.")
    return redirect(request.referrer or url_for("index"))

@app.route("/banners/<int:id>/imagem")
def banner_imagem(id:int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT imagem, imagem_mime FROM banners WHERE id=%s", (id,))
        row = cur.fetchone()
        if not row:
            abort(404)
        return send_file(BytesIO(row["imagem"]),
                         mimetype=row.get("imagem_mime") or "application/octet-stream",
                         as_attachment=False, download_name=f"banner_{id}", max_age=3600, conditional=True)

# ------------------ Contatos ------------------
@app.route("/contatos")
def contatos_page():
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, nome, telefone, email, UNIX_TIMESTAMP(criado_em) AS v "
            "FROM contatos ORDER BY id DESC"
        )
        contatos = cur.fetchall()

    for c in contatos:
        c["foto_url"] = url_for("contato_foto", id=c["id"]) + f"?v={c.get('v') or 0}"
        tel_digits = "".join(ch for ch in (c["telefone"] or "") if ch.isdigit())
        if tel_digits and not tel_digits.startswith("55"):
            tel_digits = "55" + tel_digits
        c["whats_url"] = f"https://wa.me/{tel_digits}" if tel_digits else "#"

    return render_template("contatos.html", contatos=contatos)

@app.route("/contatos", methods=["POST"])
@admin_required
def criar_contato():
    nome = (request.form.get("nome") or "").strip()
    telefone = (request.form.get("telefone") or "").strip()
    email = (request.form.get("email") or "").strip() or None
    foto = request.files.get("foto")

    if not nome or not telefone:
        flash_err("Nome e telefone são obrigatórios.")
        return redirect(request.referrer or url_for("contatos_page"))

    foto_bytes = foto_name = foto_mime = None
    if foto and foto.filename:
        if not is_image(foto):
            flash_err("Foto inválida.")
            return redirect(request.referrer or url_for("contatos_page"))
        data = foto.read()
        foto_bytes, foto_name, foto_mime = data, foto.filename, foto.mimetype

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO contatos (nome, telefone, email, foto, foto_nome, foto_mime)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (nome, telefone, email, foto_bytes, foto_name, foto_mime),
        )
    flash_ok("Contato criado.")
    return redirect(request.referrer or url_for("contatos_page"))

@app.route("/contatos/<int:id>", methods=["POST"])
@admin_required
def editar_contato(id:int):
    nome = (request.form.get("nome") or "").strip()
    telefone = (request.form.get("telefone") or "").strip()
    email = (request.form.get("email") or "").strip() or None
    foto = request.files.get("foto")

    if not nome or not telefone:
        flash_err("Nome e telefone são obrigatórios.")
        return redirect(request.referrer or url_for("contatos_page"))

    with db() as conn, conn.cursor() as cur:
        if foto and foto.filename:
            if not is_image(foto):
                flash_err("Foto inválida.")
                return redirect(request.referrer or url_for("contatos_page"))
            data = foto.read()
            cur.execute(
                """UPDATE contatos SET nome=%s, telefone=%s, email=%s,
                          foto=%s, foto_nome=%s, foto_mime=%s
                   WHERE id=%s""",
                (nome, telefone, email, data, foto.filename, foto.mimetype, id),
            )
        else:
            cur.execute(
                "UPDATE contatos SET nome=%s, telefone=%s, email=%s WHERE id=%s",
                (nome, telefone, email, id),
            )
    flash_ok("Contato atualizado.")
    return redirect(request.referrer or url_for("contatos_page"))

@app.route("/contatos/<int:id>/delete", methods=["POST"])
@admin_required
def excluir_contato(id:int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM contatos WHERE id=%s", (id,))
    flash_info("Contato excluído.")
    return redirect(request.referrer or url_for("contatos_page"))

@app.route("/contatos/<int:id>/foto")
def contato_foto(id:int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT foto, foto_mime FROM contatos WHERE id=%s", (id,))
        row = cur.fetchone()
        if not row or not row["foto"]:
            # 1x1 gif transparente
            return send_file(BytesIO(
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
                b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"),
                mimetype="image/gif")
        return send_file(BytesIO(row["foto"]),
                         mimetype=row.get("foto_mime") or "application/octet-stream",
                         as_attachment=False, download_name=f"contato_{id}", max_age=3600, conditional=True)

# ------------------ Saúde ------------------
@app.route("/_health")
def health():
    try:
        with db() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return {"ok": True, "ts": datetime.utcnow().isoformat()+"Z"}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

# ------------------ Tratadores de erro (mostram avisos) ------------------
@app.errorhandler(404)
def not_found(e):
    return render_template(
        "error.html",
        code=404,
        title="Página não encontrada",
        message="A URL que você tentou acessar não existe."
    ), 404

@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.html",
        code=500,
        title="Erro interno",
        message="Ocorreu um erro inesperado no servidor. Tente novamente mais tarde."
    ), 500

@app.errorhandler(413)  # Payload Too Large
def too_large(e):
    return render_template(
        "error.html",
        code=413,
        title="Arquivo muito grande",
        message="O arquivo enviado excede o limite permitido (8 MB)."
    ), 413


# ------------------ Execução ------------------
if __name__ == "__main__":
    app.jinja_env.globals["now"] = datetime.utcnow

    # sempre escuta em todas as interfaces (LAN/Wi-Fi)
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("DEBUG", "1") == "1"

    app.run(host=host, port=port, debug=debug)

