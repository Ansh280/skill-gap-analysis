import sqlite3, random, os
from datetime import date, timedelta

DB_PATH = "database/skill_gap.db"
os.makedirs("database", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS job_postings;
DROP TABLE IF EXISTS job_skills;
DROP TABLE IF EXISTS curriculum;
DROP TABLE IF EXISTS curriculum_skills;

CREATE TABLE job_postings (
    job_id       INTEGER PRIMARY KEY,
    company      TEXT,
    role         TEXT,
    location     TEXT,
    domain       TEXT,
    exp_level    TEXT,
    salary_lpa   REAL,
    posted_date  TEXT
);

CREATE TABLE job_skills (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id     INTEGER,
    skill      TEXT,
    category   TEXT,
    FOREIGN KEY (job_id) REFERENCES job_postings(job_id)
);

CREATE TABLE curriculum (
    course_id    INTEGER PRIMARY KEY,
    subject      TEXT,
    department   TEXT,
    semester     INTEGER,
    credit_hours INTEGER
);

CREATE TABLE curriculum_skills (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    skill     TEXT,
    category  TEXT,
    FOREIGN KEY (course_id) REFERENCES curriculum(course_id)
);
""")

# ── JOB POSTINGS DATA ──────────────────────────────────────────────────────────
companies = [
    ("TCS",            "IT Services"),
    ("Infosys",        "IT Services"),
    ("Wipro",          "IT Services"),
    ("HCL Technologies","IT Services"),
    ("Accenture",      "Consulting"),
    ("Deloitte",       "Consulting"),
    ("EY",             "Consulting"),
    ("KPMG",           "Consulting"),
    ("Zomato",         "Startup"),
    ("Swiggy",         "Startup"),
    ("PhonePe",        "Fintech"),
    ("Razorpay",       "Fintech"),
    ("Paytm",          "Fintech"),
    ("Ola",            "Startup"),
    ("Byju's",         "EdTech"),
    ("Unacademy",      "EdTech"),
    ("Meesho",         "E-Commerce"),
    ("Flipkart",       "E-Commerce"),
    ("Amazon India",   "E-Commerce"),
    ("Google India",   "Tech MNC"),
    ("Microsoft India","Tech MNC"),
    ("IBM India",      "Tech MNC"),
    ("Mu Sigma",       "Analytics"),
    ("Fractal Analytics","Analytics"),
    ("Tiger Analytics","Analytics"),
    ("Delhivery",      "Logistics"),
    ("MakeMyTrip",     "Travel"),
    ("PolicyBazaar",   "Insurtech"),
]

roles = {
    "Data Analyst": {
        "skills": ["Python","SQL","Excel","Power BI","Tableau","Pandas","NumPy",
                   "Data Visualization","Statistics","Machine Learning","ETL",
                   "Data Cleaning","DAX","Looker","A/B Testing","Business Intelligence",
                   "Communication","Problem Solving"],
        "salary_range": (4.5, 14.0),
        "exp": ["Fresher","Junior","Mid-Level"]
    },
    "Business Analyst": {
        "skills": ["SQL","Excel","Power BI","Requirement Gathering","Stakeholder Management",
                   "JIRA","Agile","Process Mapping","Communication","Data Visualization",
                   "Python","Tableau","Critical Thinking","Documentation","Presentation"],
        "salary_range": (5.0, 16.0),
        "exp": ["Fresher","Junior","Mid-Level"]
    },
    "Data Engineer": {
        "skills": ["Python","SQL","Apache Spark","Hadoop","ETL","AWS","Azure",
                   "Kafka","Airflow","Docker","Linux","Data Warehousing","Scala",
                   "Databricks","Git","Problem Solving"],
        "salary_range": (7.0, 22.0),
        "exp": ["Junior","Mid-Level","Senior"]
    },
    "ML Engineer": {
        "skills": ["Python","Machine Learning","Deep Learning","TensorFlow","PyTorch",
                   "Scikit-learn","NLP","Computer Vision","Docker","Git","AWS",
                   "Statistics","Mathematics","SQL","Research Skills"],
        "salary_range": (8.0, 28.0),
        "exp": ["Junior","Mid-Level","Senior"]
    },
    "BI Developer": {
        "skills": ["Power BI","Tableau","SQL","DAX","Excel","Data Modeling",
                   "ETL","SSRS","Azure","Data Warehousing","Communication",
                   "Stakeholder Management","Python"],
        "salary_range": (5.5, 18.0),
        "exp": ["Fresher","Junior","Mid-Level"]
    },
}

skill_categories = {
    "Python":"Programming","SQL":"Database","Excel":"Tools","Power BI":"Visualization",
    "Tableau":"Visualization","Pandas":"Programming","NumPy":"Programming",
    "Data Visualization":"Analytics","Statistics":"Math/Stats","Machine Learning":"AI/ML",
    "ETL":"Data Engineering","Data Cleaning":"Analytics","DAX":"Visualization",
    "Looker":"Visualization","A/B Testing":"Analytics","Business Intelligence":"Analytics",
    "Communication":"Soft Skills","Problem Solving":"Soft Skills","Requirement Gathering":"BA",
    "Stakeholder Management":"Soft Skills","JIRA":"Tools","Agile":"Methodology",
    "Process Mapping":"BA","Critical Thinking":"Soft Skills","Documentation":"Soft Skills",
    "Presentation":"Soft Skills","Apache Spark":"Data Engineering","Hadoop":"Data Engineering",
    "AWS":"Cloud","Azure":"Cloud","Kafka":"Data Engineering","Airflow":"Data Engineering",
    "Docker":"DevOps","Linux":"OS","Data Warehousing":"Data Engineering","Scala":"Programming",
    "Databricks":"Data Engineering","Git":"Tools","Deep Learning":"AI/ML","TensorFlow":"AI/ML",
    "PyTorch":"AI/ML","Scikit-learn":"AI/ML","NLP":"AI/ML","Computer Vision":"AI/ML",
    "Mathematics":"Math/Stats","Research Skills":"Soft Skills","Data Modeling":"Data Engineering",
    "SSRS":"Visualization","Looker":"Visualization",
}

random.seed(42)
job_rows, skill_rows = [], []
job_id = 1
base_date = date(2025, 6, 1)

for company, domain in companies:
    for role_name, role_data in roles.items():
        n_posts = random.randint(2, 5)
        for _ in range(n_posts):
            exp = random.choice(role_data["exp"])
            lo, hi = role_data["salary_range"]
            mult = {"Fresher":0.6,"Junior":0.8,"Mid-Level":1.0,"Senior":1.3}.get(exp, 1.0)
            salary = round(random.uniform(lo*mult, hi*mult*0.9), 1)
            location = random.choice(["Bengaluru","Mumbai","Delhi","Hyderabad","Pune","Chennai","Kolkata","Chandigarh"])
            days_ago = random.randint(0, 180)
            posted = (base_date + timedelta(days=days_ago)).isoformat()
            job_rows.append((job_id, company, role_name, location, domain, exp, salary, posted))

            n_skills = random.randint(6, 12)
            chosen = random.sample(role_data["skills"], min(n_skills, len(role_data["skills"])))
            for sk in chosen:
                cat = skill_categories.get(sk, "Other")
                skill_rows.append((job_id, sk, cat))
            job_id += 1

cur.executemany("INSERT INTO job_postings VALUES (?,?,?,?,?,?,?,?)", job_rows)
cur.executemany("INSERT INTO job_skills (job_id,skill,category) VALUES (?,?,?)", skill_rows)

# ── COLLEGE CURRICULUM DATA ────────────────────────────────────────────────────
curriculum_rows = [
    (1,  "Programming in C",             "CSE", 1, 4),
    (2,  "Data Structures & Algorithms", "CSE", 2, 4),
    (3,  "Object Oriented Programming",  "CSE", 3, 4),
    (4,  "Database Management Systems",  "CSE", 3, 4),
    (5,  "Operating Systems",            "CSE", 4, 4),
    (6,  "Computer Networks",            "CSE", 4, 3),
    (7,  "Software Engineering",         "CSE", 5, 3),
    (8,  "Web Technologies",             "CSE", 5, 3),
    (9,  "Artificial Intelligence",      "CSE", 6, 3),
    (10, "Machine Learning",             "CSE", 6, 3),
    (11, "Big Data Analytics",           "CSE", 6, 3),
    (12, "Mathematics I (Calculus)",     "MATH",1, 4),
    (13, "Mathematics II (Linear Alg)",  "MATH",2, 4),
    (14, "Probability & Statistics",     "MATH",3, 4),
    (15, "Business Communication",       "MGMT",2, 2),
    (16, "Principles of Management",     "MGMT",3, 3),
    (17, "Entrepreneurship",             "MGMT",5, 2),
    (18, "Computer Organization",        "CSE", 2, 3),
    (19, "Theory of Computation",        "CSE", 4, 3),
    (20, "Compiler Design",              "CSE", 5, 3),
    (21, "Python Programming",           "CSE", 4, 3),
    (22, "Java Programming",             "CSE", 3, 3),
    (23, "Data Warehousing & Mining",    "CSE", 6, 3),
    (24, "Cloud Computing Fundamentals", "CSE", 6, 3),
    (25, "Project Management",           "MGMT",6, 2),
]

curriculum_skills_data = {
    1:  [("C Programming","Programming")],
    2:  [("Data Structures","Programming"),("Algorithm Design","Programming"),("Problem Solving","Soft Skills")],
    3:  [("Java","Programming"),("OOP Concepts","Programming")],
    4:  [("SQL","Database"),("Database Design","Database"),("Data Modeling","Data Engineering")],
    5:  [("Linux","OS"),("OS Concepts","Programming")],
    6:  [("Networking","Other"),("TCP/IP","Other")],
    7:  [("Agile","Methodology"),("Documentation","Soft Skills"),("SDLC","Other")],
    8:  [("HTML/CSS","Programming"),("JavaScript","Programming"),("PHP","Programming")],
    9:  [("AI Concepts","AI/ML"),("Search Algorithms","AI/ML"),("Logic Programming","AI/ML")],
    10: [("Machine Learning","AI/ML"),("Scikit-learn","AI/ML"),("Statistics","Math/Stats"),("Python","Programming")],
    11: [("Hadoop","Data Engineering"),("Big Data Concepts","Data Engineering"),("Data Analysis","Analytics")],
    12: [("Mathematics","Math/Stats"),("Calculus","Math/Stats")],
    13: [("Mathematics","Math/Stats"),("Linear Algebra","Math/Stats"),("NumPy","Programming")],
    14: [("Statistics","Math/Stats"),("Probability","Math/Stats"),("Data Analysis","Analytics")],
    15: [("Communication","Soft Skills"),("Presentation","Soft Skills"),("Documentation","Soft Skills")],
    16: [("Management","Soft Skills"),("Stakeholder Management","Soft Skills"),("Critical Thinking","Soft Skills")],
    17: [("Problem Solving","Soft Skills"),("Research Skills","Soft Skills")],
    18: [("Computer Architecture","Other")],
    19: [("Automata Theory","Other")],
    20: [("Compiler Theory","Other")],
    21: [("Python","Programming"),("Pandas","Programming"),("Data Cleaning","Analytics"),("NumPy","Programming")],
    22: [("Java","Programming"),("OOP Concepts","Programming")],
    23: [("Data Warehousing","Data Engineering"),("ETL","Data Engineering"),("Data Mining","Analytics")],
    24: [("AWS","Cloud"),("Cloud Basics","Cloud"),("Azure","Cloud")],
    25: [("JIRA","Tools"),("Agile","Methodology"),("Project Planning","Soft Skills"),("Documentation","Soft Skills")],
}

cur.executemany("INSERT INTO curriculum VALUES (?,?,?,?,?)", curriculum_rows)
for course_id, skills in curriculum_skills_data.items():
    for skill, cat in skills:
        cur.execute("INSERT INTO curriculum_skills (course_id,skill,category) VALUES (?,?,?)",
                    (course_id, skill, cat))

conn.commit()
print(f"DB created: {len(job_rows)} job postings, {len(skill_rows)} skill records")
conn.close()
