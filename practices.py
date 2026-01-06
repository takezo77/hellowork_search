import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'hellowork.db')








app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRCK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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
    expiry_date = db.Column(db.Text) 


class job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    