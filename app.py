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
    job_category = db.Column(db.Text); company_name = db.Column(db.Text)
    work_location = db.Column(db.Text); job_description = db.Column(db.Text)
    employment_type = db.Column(db.Text); salary = db.Column(db.Text)
    working_hours = db.Column(db.Text); holidays = db.Column(db.Text)
    age_limit = db.Column(db.Text); job_number = db.Column(db.Text)
    disclosure_scope = db.Column(db.Text); detail_url = db.Column(db.Text)
    pdf_url = db.Column(db.Text); reception_date = db.Column(db.Text); expiry_date = db.Column(db.Text)

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


PREFECTURES = [
    ("01", "北海道"), ("02", "青森県"), ("03", "岩手県"), ("04", "宮城県"), ("05", "秋田県"),
    ("06", "山形県"), ("07", "福島県"), ("08", "茨城県"), ("09", "栃木県"), ("10", "群馬県"),
    ("11", "埼玉県"), ("12", "千葉県"), ("13", "東京都"), ("14", "神奈川県"), ("15", "新潟県"),
    ("16", "富山県"), ("17", "石川県"), ("18", "福井県"), ("19", "山梨県"), ("20", "長野県"),
    ("21", "岐阜県"), ("22", "静岡県"), ("23", "愛知県"), ("24", "三重県"), ("25", "滋賀県"),
    ("26", "京都府"), ("27", "大阪府"), ("28", "兵庫県"), ("29", "奈良県"), ("30", "和歌山県"),
    ("31", "鳥取県"), ("32", "島根県"), ("33", "岡山県"), ("34", "広島県"), ("35", "山口県"),
    ("36", "徳島県"), ("37", "香川県"), ("38", "愛媛県"), ("39", "高知県"), ("40", "福岡県"),
    ("41", "佐賀県"), ("42", "長崎県"), ("43", "熊本県"), ("44", "大分県"), ("45", "宮崎県"),
    ("46", "鹿児島県"), ("47", "沖縄県")
]

@app.route("/", methods=["GET", "POST"])
def index():
    query = Job.query
    keyword = request.form.get("keyword", "")
    area = request.form.get("area", "")
    
    # Get selected prefecture from query param (defaults to Mie 24)
    selected_prefecture = request.args.get("pref", "24")
    selected_prefecture_name = dict(PREFECTURES).get(selected_prefecture, "三重県")

    if keyword:
        query = query.filter(Job.job_description.contains(keyword))
    if area:
        query = query.filter(Job.work_location.contains(area))
        
    return render_template("index.html", 
                         jobs=query.all(), 
                         keyword=keyword, 
                         area=area,
                         prefectures=PREFECTURES,
                         selected_prefecture=selected_prefecture,
                         selected_prefecture_name=selected_prefecture_name)

@app.route("/update_data", methods=["POST"])
def update_data():
    prefecture_code = request.form.get("prefecture", "24")
    subprocess.run([sys.executable, "scrape.py", prefecture_code], check=True)
    return redirect(url_for('index', pref=prefecture_code))

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

@app.route("/export_selected", methods=["POST"])
def export_selected():
    selected_ids = request.form.getlist('selected_ids')
    if not selected_ids:
        return redirect(url_for('my_list_view'))
    
    # Selected jobs query
    jobs_to_export = MyList.query.filter(MyList.id.in_(selected_ids)).all()
    
    # Init list for dataframe
    data = []
    for job in jobs_to_export:
        data.append({
            "求人番号": job.job_number,
            "職種": job.job_category,
            "会社名": job.company_name,
            "就業場所": job.work_location,
            "仕事内容": job.job_description,
            "雇用形態": job.employment_type,
            "賃金": job.salary,
            "就業時間": job.working_hours, 
            "休日": job.holidays,
            "年齢": job.age_limit,
            "公開範囲": job.disclosure_scope,
            "詳細URL": job.detail_url,
            "求人票PDF": job.pdf_url,
            "受付年月日": job.reception_date,
            "紹介期限日": job.expiry_date
        })

    df = pd.DataFrame(data)
    
    # Save to a temporary file (or directly to memory, but file is safer for send_file in this setup)
    filename = "hellowork_selected_export.xlsx"
    df.to_excel(filename, index=False)
    
    return send_file(filename, as_attachment=True)

@app.route("/export")
def export():
    df = pd.read_sql("SELECT * FROM jobs", db.engine)
    df.to_excel("hellowork_full_export.xlsx", index=False)
    return send_file("hellowork_full_export.xlsx", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5000)