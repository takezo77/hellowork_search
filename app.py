from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
import pandas as pd
import os, subprocess, sys

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'hellowork.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
db = SQLAlchemy(app)

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    job_category = db.Column(db.Text)
    company_name = db.Column(db.Text)
    work_location = db.Column(db.Text)
    job_description = db.Column(db.Text)
    employment_type = db.Column(db.Text)
    salary = db.Column(db.Text)
    working_hours = db.Column(db.Text)
    holidays = db.Column(db.Text)
    age_limit = db.Column(db.Text)
    job_number = db.Column(db.Text)
    disclosure_scope = db.Column(db.Text)
    detail_url = db.Column(db.Text)
    pdf_url = db.Column(db.Text)
    reception_date = db.Column(db.Text) # ここが正しく読み取られる必要があります
    expiry_date = db.Column(db.Text)    # ここが正しく読み取られる必要があります

class MyList(db.Model):
    __tablename__ = 'my_list'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, unique=True)
    job_category = db.Column(db.Text); 
    company_name = db.Column(db.Text)
    work_location = db.Column(db.Text); 
    job_description = db.Column(db.Text)
    employment_type = db.Column(db.Text); 
    salary = db.Column(db.Text)
    working_hours = db.Column(db.Text); 
    holidays = db.Column(db.Text)
    age_limit = db.Column(db.Text); 
    job_number = db.Column(db.Text)
    disclosure_scope = db.Column(db.Text); 
    detail_url = db.Column(db.Text)
    pdf_url = db.Column(db.Text); 
    reception_date = db.Column(db.Text); 
    expiry_date = db.Column(db.Text)

def repair_db():
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        for table in ['jobs', 'my_list']:
            existing = [c['name'] for c in inspector.get_columns(table)]
            for col in ['reception_date', 'expiry_date', 'detail_url', 'pdf_url']:
                if col not in existing:
                    with db.engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} TEXT"))
                        conn.commit()

with app.app_context(): repair_db()

@app.route("/", methods=["GET", "POST"])
def index():
    query = Job.query
    keyword = request.form.get("keyword", ""); area = request.form.get("area", "")
    if keyword: query = query.filter(Job.job_description.contains(keyword))
    if area: query = query.filter(Job.work_location.contains(area))
    return render_template("index.html", jobs=query.all(), keyword=keyword, area=area)

@app.route("/update_data")
def update_data():
    try:
        # 子プロセスに現在の環境変数（Playwrightのパスなど）を引き継がせる
        import os
        env = os.environ.copy()
        
        # scrape.py を実行
        subprocess.run([sys.executable, "scrape.py"], check=True, env=env)
        
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        # エラーが起きた場合にブラウザで確認できるようにする
        return f"スクレイピング失敗: {e}", 500

@app.route("/add_to_list/<int:job_id>")
def add_to_list(job_id):
    j = Job.query.get_or_404(job_id)
    if not MyList.query.filter_by(job_id=job_id).first():
        new_item = MyList(job_id=j.id, job_category=j.job_category, company_name=j.company_name, work_location=j.work_location, job_description=j.job_description, employment_type=j.employment_type, salary=j.salary, working_hours=j.working_hours, holidays=j.holidays, age_limit=j.age_limit, job_number=j.job_number, disclosure_scope=j.disclosure_scope, detail_url=j.detail_url, pdf_url=j.pdf_url, reception_date=j.reception_date, expiry_date=j.expiry_date)
        db.session.add(new_item); db.session.commit()
    return redirect(url_for('index'))

@app.route("/list")
def my_list_view():
    return render_template("list.html", saved_jobs=MyList.query.all())

@app.route("/delete_item/<int:item_id>")
def delete_item(item_id):
    db.session.delete(MyList.query.get_or_404(item_id)); db.session.commit()
    return redirect(url_for('my_list_view'))

@app.route("/export")
def export():
    df = pd.read_sql("SELECT * FROM jobs", db.engine)
    df.to_excel("hellowork_full_export.xlsx", index=False)
    return send_file("hellowork_full_export.xlsx", as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render用
    app.run(host="0.0.0.0", port=port)