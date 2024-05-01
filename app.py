from flask import Flask, jsonify, request, send_from_directory, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename
import os
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from datetime import datetime

from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
api = Api(app)
CORS(app, resources = {
	r"/*": {"origins" : "*"}
})

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://dilip:VasmiGroup#123@154.41.253.135:5432/aadhya'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:SaiPrasanth@localhost:5432/aadhya'
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a secure random key in a real applicationdb = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['IMAGE_FOLDER'] = 'images'


db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

admin = Admin(app)


# Database Models

class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=True, unique=True)

    def __repr__(self) -> str:
        return f'{self.full_name}'
    



class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255), nullable = False)
    image = db.Column(db.String(255), nullable = False)
    posted_date = db.Column(db.Date, default=datetime.today, nullable=True)
    description = db.Column(db.Text, nullable= False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self) -> str:
        return f'Blog Post - {self.id} - {self.title}'

class FormData(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    loanType = db.Column(db.String(255), nullable = True)
    position = db.Column(db.String(255), nullable = True)
    carName = db.Column(db.String(255), nullable = True)
    loanAmount = db.Column(db.String(255), nullable = False)
    loanTenure = db.Column(db.String(255), nullable = True)
    type = db.Column(db.String(255), nullable = True)
    firstName = db.Column(db.String(255), nullable = False)
    lastName = db.Column(db.String(255), nullable = False)
    address = db.Column(db.String(255), nullable = True)
    state = db.Column(db.String(255), nullable = True)
    zipcode = db.Column(db.String(255), nullable = True)
    city = db.Column(db.String(255), nullable = True)
    phoneNumber = db.Column(db.String(255), nullable = False)
    dob = db.Column(db.Date, nullable = False)
    email = db.Column(db.String(255), nullable = False)
    single = db.Column(db.String(255), nullable = True)
    image = db.Column(db.String, nullable = False)
    document = db.Column(db.String, nullable = False)
    pdf = db.Column(db.String, nullable = False)

    def __repr__(self) -> str:
        return f" {self.firstName} "

class Subscribers(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(255), nullable = False)

    def __repr__(self) -> str:
        return f"{self.id} - {self.email}"



@login_manager.user_loader
def load_user(user_id):
    return users.query.get(int(user_id))

class AdminModelView(ModelView):
    column_exclude_list = ['password']

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin


class BlogAdminView(AdminModelView):
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True

    form_columns = ('title', 'image_doc', 'posted_date', 'description', 'content')

    form_extra_fields = {
        'image_doc': FileUploadField('Image File', base_path='images/')
    }

    def on_model_change(self, form, model, is_created):
        if form.image_doc._value:
            model.image = form.image_doc.data.filename


class UserAdminView(AdminModelView):
    column_list = ['id', 'email']

admin.add_view(UserAdminView(users, db.session, name='My Users'))
admin.add_view(AdminModelView(FormData, db.session, name='Leads'))
admin.add_view(BlogAdminView(BlogPost, db.session, name='Blog Posts'))
admin.add_view(AdminModelView(Subscribers, db.session, name='Subscribers'))


# Swagger Documentation for API Endpoints

SWAGGER_URL="/swagger"
API_URL="/static/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Access API'
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


# USER AUTHENTICATION

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("request type method:", request.method)
    if request.method == 'POST':
        print("request type method:", request.method)
        username = request.form['username']
        password = request.form['password']
        mobile = request.form['mobile']
        dob = request.form['dob']

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            new_user = users(full_name=username ,mobile = mobile, password=hashed_password, dob = dob)

            db.session.add(new_user)
            db.session.commit()

            print("Sign up Successful! Please log in.", "success")
        except Exception as e:
            print("An error has occurred", "error")
        return redirect(url_for('login'))

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']
        try:
            user = users.query.filter_by(mobile=mobile).first()
            print(password)
            print(check_password_hash(user.password, password))
            if user and check_password_hash(user.password, password):
                login_user(user)
                print("Login Successful!", 'success')
                return redirect(url_for('admin.index'))
            else:
                print('Login failed. Please check your username and password.', 'error')
                return render_template('login.html')
        except Exception as e:
            print("An error has occurred", "error")

    return render_template('login.html')


@app.route('/reset_password')
def reset_password():
    if request.method == 'POST':
        # Update Database with the new password for the user
        mobile = extract_mobile_number(mobile)
        try:
            user = users.query.filter_by(mobile = mobile).first()
            new_password = request.form['pass1']

            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            user.password = hashed_password

            db.session.commit()
        except Exception as e:
            print("An error has occurred: ",e)


        return redirect(url_for('login'))
    return render_template('reset_password.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    print('Logout successful!')
    return redirect(url_for('login'))

#END OF USER AUTHENTICATION


def extract_mobile_number(full_number):
    # Remove any non-digit characters
    numeric_part = ''.join(filter(str.isdigit, full_number))
    # Keep only the last 10 digits
    mobile_number = numeric_part[-10:]
    return mobile_number

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']

    try:
        new_subscriber = Subscribers(email = email)
        db.session.add(new_subscriber)
        db.session.commit()

        return jsonify({
            'result': 'Subscriber Saved'
        })
    except Exception as e:
        print(e)
        
        return jsonify({
            'result': 'Subscriber not saved'
        })


@app.route("/api/apply", methods=['POST'])
def form_submit():
    loanType = request.form['loanType']
    position = request.form['position']
    carName = request.form['carName']
    loanAmount = request.form['loanAmount'] 
    loanTenure = request.form['loanTenure'] 
    type = request.form['type'] 
    firstName = request.form['firstName'] 
    lastName = request.form['lastName'] 
    address = request.form['address'] 
    state = request.form['state'] 
    zipcode = request.form['zipcode'] 
    city = request.form['city'] 
    phoneNumber = request.form['phoneNumber'] 
    dob = request.form['dob'] 
    email = request.form['email'] 
    single = request.form['single']
    image = request.files['image']
    document = request.files['document']
    pdf = request.files['pdf']

    image_filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image.filename))
    image.save(image_filepath)

    document_filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(document.filename))
    document.save(document_filepath)

    pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pdf.filename))
    pdf.save(pdf_filepath)
    try:
        new_formData = FormData(
            loanType = loanType,
            position = position,
            carName = carName,
            loanAmount = loanAmount , 
            loanTenure = loanTenure, 
            type = type, 
            firstName = firstName, 
            lastName = lastName, 
            address = address, 
            state = state, 
            zipcode = zipcode, 
            city = city, 
            phoneNumber = phoneNumber, 
            dob = dob, 
            email = email, 
            single = single,
            image= image_filepath,
            document = document_filepath,
            pdf = pdf_filepath
        )

        db.session.add(new_formData)
        db.session.commit()




        return jsonify({
            "result": "Form Data saved Successfully!"
        })
    except Exception as e:
        print(e)
        return jsonify({
            "result": "Failed to save Form Data!"
        }) 


# @app.route("/blogposts")
# def blogposts():
#     posts = BlogPost.query.all()
#     print(posts)
#     return jsonify([{'id': post.id, 'title': post.title, 'content': post.content} for post in posts])

@app.route("/api/blogposts")
def blogposts():
    try:
        posts = BlogPost.query.all()
        print(posts)
        return jsonify([{
            'id': post.id,
            'title': post.title, 
            'image': f'https://www.aadhyacarloans.com/api/images/{post.image}',
            'posted_date': post.posted_date,
            'description': post.description,
            'content': post.content
            } for post in posts])
    except Exception as e:
        print(e)
        return jsonify({
            'error': e
        })


@app.route('/api/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)



@app.route("/test", methods=['POST'])
def test():
    t1 = request.form['t1']
    print(t1)

    return jsonify({
        'result': 'Data Recieved!'
    })

#  Create Database Tables while initial Run
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
