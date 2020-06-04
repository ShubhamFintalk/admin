import datetime
import  time
import peewee as pw
from django.shortcuts import redirect
from flask import Flask, render_template, request, url_for
from template import render
db = pw.SqliteDatabase('attendance.db')

class User(pw.Model):
    uid = pw.CharField(unique = True)
    name = pw.CharField()
    clas = pw.CharField(null = True)
    folder_name = pw.CharField()

    def __str__(self):
        return "{0}, Id: {2}, Name: {1}, Class: {2}".format(self.id, self.name, self.uid, self.clas)

    class Meta:
        database = db

class Attendance(pw.Model):
    user = pw.ForeignKeyField(User, backref='records')
    time = pw.DateTimeField(default=datetime.date.today)
    dot_score = pw.FloatField()
    diff_score = pw.FloatField()

    def __str__(self):
        return "User: {0}, Time: {1}, Dot Score: {2}, Diff Score: {3}"\
            .format(self.user, self.time, self.dot_score, self.diff_score)

    class Meta:
        database = db

class Annotation(pw.Model):
    user = pw.ForeignKeyField(User, backref='files')
    fname = pw.CharField()
    rect = pw.CharField(max_length=2000)

    class Meta:
        database = db

def get_present():
    f1 = pw.fn.MAX(Attendance.time).alias('max')
    f2 = pw.fn.MIN(Attendance.time).alias('min')
    q = Attendance.select(User.name, f1, f2)\
            .where(Attendance.time >= datetime.date.today())\
            .join(User)\
            .group_by(Attendance.user)\
            .dicts()

    return list(q)

def get_absent():
    # q = User.select(User.uid, User.name).where(~pw.fn.EXISTS(Attendance.select().where(
    # 		(Attendance.user == User.id) & (Attendance.time >= datetime.date.today()))))
    return [{'name': name} for name in (set([e['name'] for e in list(User.select(User.name).dicts())])
             - set([e['name'] for e in get_present()]))]
db.connect()
db.create_tables([User, Attendance, Annotation])
Date_str=[str(i.time.date()) for i in Attendance.select()]
Time_str=[str(i.time.time()) for i in Attendance.select()]
list_of_Dates=list(dict.fromkeys(Date_str))
list_of_Times=list(dict.fromkeys(Time_str))
Total_Student=len([Id.uid for Id in User.select()])
Total_days=len(list_of_Dates)

app=Flask(__name__, static_folder="assets", template_folder="templates")
'''
In_Out_Time = []
Time_In_Out = Attendance.select(Attendance.user, pw.fn.Min(pw.fn.time(Attendance.time)),
                                        pw.fn.Max(pw.fn.time(Attendance.time))) \
            .join(User).where(pw.fn.date(Attendance.time) == datetime.date.today()).distinct().group_by(Attendance.user.id).tuples()
for In in Time_In_Out:
    Info = Attendance.select(Attendance.user).join(User).where(Attendance.user.id == In[0]).distinct()
    for u in Info:
        p = In[1]
        q=In[2]
        FMT = '%H:%M:%S'
        Int_In = str(datetime.datetime.strptime(p, FMT).time())
        Int_Out = str(datetime.datetime.strptime(q, FMT).time())
        Total_hours = datetime.datetime.strptime(Int_Out, FMT) - datetime.datetime.strptime(Int_In, FMT)
        InOut = (datetime.date.today(), u.user.name, u.user.clas, In[1], In[2],Total_hours)
        In_Out_Time.append(InOut)

'''
#Module for Home page [Dashboard]
@app.route('/',methods=['POST','GET'])
def index():
    This_Month_Attendance=[]
    Present=Attendance.select(Attendance.user).join(User).where(pw.fn.date(Attendance.time)==datetime.date.today()).distinct().count()
    This_Month=datetime.date.today(),Total_Student,Present,Total_Student-Present
    This_Month_Attendance.append(This_Month)
    Month=[]
    if request.method=="POST":
        month=request.form['MonthDate']
        FMT = '%Y-%m'
        MonthWise_Attendance = []
        Month_str = datetime.datetime.strptime(month, FMT).date()  # 2019-05-01
        next_month = Month_str.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
        End_month_date = next_month - datetime.timedelta(days=next_month.day)
        Present1 = Attendance.select(Attendance.time, Attendance.user).join(User).where(
            pw.fn.date(Attendance.time).between(Month_str, End_month_date))
        Date_st = [str(i.time.date()) for i in Present1]
        Months_Dates = list(dict.fromkeys(Date_st))
        for i in Months_Dates:
            Present2 = Attendance.select(Attendance.user).join(User).where(
                pw.fn.date(Attendance.time) == i).distinct().count()
            This_Month1 = [i, Total_Student, Present2, Total_Student - Present2]
            MonthWise_Attendance.append(This_Month1)
        return render_template('index.html', MonthWise=MonthWise_Attendance,This_Month_Attendance_html=This_Month_Attendance)
    return render_template('index.html',This_Month_Attendance_html=This_Month_Attendance,MonthWise=[])

#Module for Total Attendance
@app.route('/jquery-datatable')
def jquery_data():
    In_Out_Time = []
    for Dates in list_of_Dates:
        Time_In_Out = Attendance.select(Attendance.user, pw.fn.Min(pw.fn.time(Attendance.time)),
                                        pw.fn.Max(pw.fn.time(Attendance.time))) \
            .join(User).where(pw.fn.date(Attendance.time) == Dates).distinct().group_by(Attendance.user.id).tuples()
        for In in Time_In_Out:
            Info = Attendance.select(Attendance.user).join(User).where(Attendance.user.id == In[0]).distinct()
            for u in Info:
                p = In[1]
                q=In[2]
                FMT = '%H:%M:%S'
                Int_In = str(datetime.datetime.strptime(p, FMT).time())
                Int_Out = str(datetime.datetime.strptime(q, FMT).time())
                Total_hours = datetime.datetime.strptime(Int_Out, FMT) - datetime.datetime.strptime(Int_In, FMT)
                InOut = (Dates, u.user.name, u.user.clas, In[1], In[2],Total_hours)
                In_Out_Time.append(InOut)
    return render_template('jquery-datatable.html',Record=In_Out_Time)

#Module for Attendance Status EmployeeWise
@app.route('/search-results',methods=["GET","POST"])
def search_results():
    if request.method=="POST":
        Start_date=request.form['StartDate']
        End_date=request.form['EndDate']
        User_name=request.form['UserName']
        Depart_name=request.form['DepartName']

        # To calculate total company ON days
        Search_query1 = Attendance.select(Attendance.user, Attendance.time) \
        .join(User).where(Attendance.time.between(Start_date, End_date)) \
        .distinct().group_by(Attendance.time)
        Dates11 = [str(i.time.date()) for i in Search_query1]  # List of dates of all emp
        PresentDates1 = list(dict.fromkeys(Dates11))  # list of dates sorted(remove duplicate dates)
        Company_On_days = len(PresentDates1)  # total count of dates

        # To find the particular attendance of emp date wise
        Search_query = Attendance.select(Attendance.user, Attendance.time) \
        .join(User).where(User.name.contains(User_name), User.folder_name.contains(Depart_name),
                          Attendance.time.between(Start_date, End_date)) \
        .distinct().group_by(Attendance.time)
        Dates1 = [str(i.time.date()) for i in Search_query]  # list of dates of emp
        PresentDates = list(dict.fromkeys(Dates1))  # list of dates of emp sorted(remove duplicates dates)
        Emp_present = len(PresentDates)  # total count of dates

        #Employee Info
        Info = [[i.user.name, i.user.folder_name, i.user.uid] for i in Search_query]
        Info_Emp = Info[0]
        print(Info_Emp)
        Search_Table2 = [] # Table-Attendance detail variable

        #for IN-OUT time
        for Date1 in PresentDates:
            Search_Time_In_Out = Attendance.select(Attendance.user, pw.fn.Min(pw.fn.time(Attendance.time)),
                                               pw.fn.Max(pw.fn.time(Attendance.time))) \
            .join(User).where(pw.fn.date(Attendance.time) == Date1, User.name.contains(User_name)).distinct().tuples()
            for In in Search_Time_In_Out:
                Search_data_list = (Date1, In[1], In[2])
                Search_Table2.append(Search_data_list)

                #EmpInfo = list(dict.fromkeys(Info))  # List of employee name,department,UID
                Search_Table1 = [Company_On_days, Emp_present,Company_On_days - Emp_present]  # Table-Attendance Status [Total,Present, Absent]
        return render_template('search-results.html',Table2=Search_Table2, EmpInfo=Info_Emp, Table1=Search_Table1,date1=Start_date,date2=End_date)
    return render_template('search-results.html',EmpInfo=[])

if __name__=="__main__":
    app.run(debug=True)
