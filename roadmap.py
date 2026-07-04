ROADMAPS = {

    "machine": {

        "projects": [
            "House Price Prediction",
            "Movie Recommendation System",
            "Spam Email Classifier",
            "AI Chatbot"
        ],

        "extra_steps": [
            "Build ML Projects",
            "Learn Model Deployment",
            "Practice ML Algorithms"
        ]
    },

    "data": {

        "projects": [
            "Sales Dashboard",
            "Netflix Data Analysis",
            "Customer Segmentation",
            "Business Insights Dashboard"
        ],

        "extra_steps": [
            "Practice SQL Queries",
            "Build Power BI Dashboards",
            "Learn Data Visualization"
        ]
    },

    "developer": {

        "projects": [
            "Portfolio Website",
            "E-commerce Website",
            "Task Manager App",
            "Blog Application"
        ],

        "extra_steps": [
            "Build Full Stack Projects",
            "Learn APIs",
            "Deploy Applications"
        ]
    },
        "cyber": {

    "projects": [
        "Port Scanner",
        "Password Strength Checker",
        "Network Packet Analyzer",
        "Vulnerability Scanner"
    ],

    "extra_steps": [
        "Learn Networking Basics",
        "Practice Linux Commands",
        "Learn Ethical Hacking"
    ]
},

"cloud": {

    "projects": [
        "AWS Static Website Hosting",
        "Cloud File Storage System",
        "Dockerized Web App",
        "CI/CD Deployment Pipeline"
    ],

    "extra_steps": [
        "Learn AWS Services",
        "Practice Docker",
        "Learn Kubernetes Basics"
    ]
},

"devops": {

    "projects": [
        "CI/CD Pipeline Project",
        "Docker Deployment",
        "Monitoring Dashboard",
        "Kubernetes Deployment"
    ],

    "extra_steps": [
        "Learn Docker",
        "Learn Jenkins",
        "Practice Kubernetes"
    ]
},
    "analyst": {

    "projects": [
        "Customer Churn Analysis",
        "A/B Testing Analysis",
        "Product Metrics Dashboard",
        "User Behavior Analysis"
    ],

    "extra_steps": [
        "Learn Product Metrics",
        "Practice SQL Analytics",
        "Learn A/B testing"]

},
"scientist": {

    "projects": [
        "House Price Prediction",
        "Customer Segmentation",
        "Recommendation System",
        "Fraud Detection"
    ],

    "extra_steps": [
        "Learn Statistics",
        "Master Machine Learning",
        "Learn Model Deployment"
    ]
}

}

SKILL_LEARNING_STEPS = {
    "numpy": "Master NumPy through hands-on numerical computing and vectorized performance exercises.",
    "pandas": "Practice Pandas by cleaning, transforming, and summarizing a real dataset end-to-end.",
    "matplotlib": "Create clear, publication-ready visualizations with Matplotlib charts and plots.",
    "seaborn": "Use Seaborn to explore data patterns with statistical visualizations and heatmaps.",
    "scikit-learn": "Build, validate, and compare ML models using scikit-learn pipelines and metrics.",
    "sql": "Write SQL queries to join, group, and analyze relational data for business insights.",
    "power bi": "Build interactive Power BI dashboards that surface insights from business data.",
    "tableau": "Create data visualizations and dashboards using Tableau's analytics features.",
    "excel": "Use Excel for data analysis, pivot tables, formulas, and business reporting.",
    "tensorflow": "Build and train neural networks using TensorFlow for practical ML tasks.",
    "pytorch": "Practice PyTorch model development and experiment with deep learning workflows.",
    "aws": "Explore core AWS services and build a cloud-hosted data or ML proof of concept.",
    "docker": "Containerize an application with Docker to make development and deployment reproducible.",
    "kubernetes": "Learn Kubernetes fundamentals to run containerized applications at scale.",
    "nlp": "Study NLP techniques for cleaning text, extracting meaning, and building models.",
    "llm": "Experiment with large language models and prompt design for real-world tasks.",
    "prompt engineering": "Practice writing prompts that generate useful, accurate AI outputs.",
    "ab testing": "Learn A/B testing design and analyze experiment results to improve decisions.",
    "business intelligence": "Practice turning data into actionable business insights and reports.",
    "data modeling": "Practice structuring data for analytics, reporting, and business workflows."
}

ROLE_CORE_STEPS = {
    "scientist": "Practice core data science workflows: feature engineering, model validation, and interpretability.",
    "analyst": "Build analysis dashboards and reports that answer business questions with data.",
    "machine": "Practice machine learning end-to-end: data prep, model building, and evaluation.",
    "cyber": "Focus on cybersecurity fundamentals, incident analysis, and defense tools.",
    "cloud": "Build a cloud-based solution using core services and deploy it end-to-end.",
    "devops": "Practice CI/CD automation and infrastructure as code for reliable deployments.",
    "data": "Improve data literacy by practicing extraction, cleaning, and visualization workflows.",
    "developer": "Build and deploy a real app that integrates frontend, backend, and data flow."
}

SKILL_PROJECTS = {
    "numpy": [
        "Numerical Data Analysis Project",
        "Feature Engineering with NumPy"
    ],
    "pandas": [
        "Data Cleaning and Reporting Project",
        "Exploratory Data Analysis with Pandas"
    ],
    "matplotlib": [
        "Visual Analytics Dashboard",
        "Custom Charting and Data Storytelling"
    ],
    "seaborn": [
        "Statistical Visualization Project",
        "Correlation Analysis Dashboard"
    ],
    "scikit-learn": [
        "Supervised ML Model Project",
        "Model Comparison and Tuning"
    ],
    "sql": [
        "Business Data Query Project",
        "Relational Database Analysis"
    ],
    "power bi": [
        "Power BI Sales Dashboard",
        "Interactive Business Intelligence Report"
    ],
    "tableau": [
        "Tableau Performance Dashboard",
        "Executive Analytics Dashboard"
    ],
    "tensorflow": [
        "Neural Network Training Project",
        "Deep Learning Model Pipeline"
    ],
    "pytorch": [
        "PyTorch Image Classification Project",
        "Deep Learning Research Prototype"
    ],
    "aws": [
        "Cloud Data Pipeline Project",
        "Serverless Analytics Application"
    ],
    "docker": [
        "Containerized Deployment Project",
        "Dockerized Data Pipeline"
    ],
    "kubernetes": [
        "Kubernetes Deployment Project",
        "Scalable Containerized Application"
    ],
    "nlp": [
        "Text Classification Project",
        "Sentiment Analysis Application"
    ],
    "llm": [
        "AI Chatbot Project",
        "Prompt-Driven Assistant"
    ],
    "prompt engineering": [
        "Prompt Optimization Project",
        "AI Task Automation Workflow"
    ],
    "ab testing": [
        "A/B Test Experiment Analysis",
        "Conversion Optimization Case Study"
    ],
    "business intelligence": [
        "Executive Insights Dashboard",
        "Business Metrics Reporting Project"
    ],
    "data modeling": [
        "Data Warehouse Design Project",
        "Data Pipeline Modeling"
    ]
}

ROLE_ALIASES = {
    "data scientist": "scientist",
    "junior data scientist": "scientist",
    "data analyst": "analyst",
    "business analyst": "analyst",
    "product analyst": "analyst",
    "ml engineer": "machine",
    "ai engineer": "machine",
    "cyber security analyst": "cyber",
    "soc analyst": "cyber",
    "cloud engineer": "cloud",
    "devops engineer": "devops",
    "power bi developer": "data",
    "bi developer": "data"
}


def generate_roadmap(missing_skills, job_title):
    normalized_missing = [skill.strip().lower() for skill in missing_skills if skill and str(skill).strip()]
    roadmap = []
    title = str(job_title).lower()

    def get_role_category(title_text):
        for alias, category in ROLE_ALIASES.items():
            if alias in title_text:
                return category
        for role in ROADMAPS:
            if role in title_text:
                return role
        if "analyst" in title_text or "data" in title_text:
            return "data"
        return "scientist"

    def get_skill_steps(skills):
        steps = []
        for skill in skills:
            step = SKILL_LEARNING_STEPS.get(skill)
            if not step:
                step = f"Learn {skill} through hands-on practice and projects."
            if step not in steps:
                steps.append(step)
            if len(steps) >= 3:
                break
        return steps

    def get_role_step(role_key):
        return ROLE_CORE_STEPS.get(role_key)

    def get_project_suggestions(skills, role_projects):
        suggestions = []
        project_set = set()

        for skill in skills:
            if skill in SKILL_PROJECTS:
                for project in SKILL_PROJECTS[skill]:
                    if project not in project_set:
                        suggestions.append(project)
                        project_set.add(project)
                    if len(suggestions) >= 4:
                        return suggestions

        for project in role_projects:
            if project not in project_set:
                suggestions.append(project)
                project_set.add(project)
            if len(suggestions) >= 4:
                break

        return suggestions

    role = get_role_category(title)
    role_data = ROADMAPS.get(role, ROADMAPS["data"])
    projects = get_project_suggestions(normalized_missing, role_data["projects"])

    roadmap.extend(get_skill_steps(normalized_missing))

    role_step = get_role_step(role)
    if role_step and role_step not in roadmap:
        roadmap.append(role_step)

    for step in role_data["extra_steps"]:
        if step not in roadmap:
            roadmap.append(step)
        if len(roadmap) >= 5:
            break

    if normalized_missing and len(roadmap) < 5:
        top_skills = normalized_missing[:2]
        project_step = f"Build a project using {' and '.join(top_skills)}."
        if project_step not in roadmap:
            roadmap.append(project_step)

    if not roadmap:
        roadmap = [
            "Build practical projects",
            "Practice the role's most important skills",
            "Refine your resume for the target job"
        ]

    return {
        "roadmap": roadmap[:5],
        "projects": projects
    }

