import streamlit as st
from auth import (
    create_user,
    login_user,
    save_report,
    get_reports
)
import pandas as pd
import PyPDF2
import re
import requests
import uuid
from recommender import categorize_missing_skills, generate_resume_suggestions_gemini, recommend_jobs, generate_ai_insights
from roadmap import generate_roadmap
from skills_utils import extract_skills as extract_skills_from_utils, SKILL_DB, SKILL_ALIASES
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def build_fallback_chat_reply(user_query, skills, job_title):
    skills_text = ", ".join(skills[:5]) if skills else "your current background"
    job_text = job_title or "your target role"
    user_query_lower = (user_query or "").lower()

    if any(word in user_query_lower for word in ["salary", "pay", "money", "package"]):
        return (
            f"For {job_text}, a strong path is to build proof of impact in {skills_text}, then target roles with clear salary growth. "
            "Show measurable projects, internships, and results in your resume."
        )

    if any(word in user_query_lower for word in ["resume", "cv", "ats"]):
        return (
            f"For {job_text}, improve your resume by highlighting {skills_text} and adding project outcomes, metrics, and role-specific keywords."
        )

    return (
        f"For {job_text}, focus on strengthening {skills_text}, adding practical projects, and tailoring your resume to the role. "
        "If you want, I can also help you turn this into a step-by-step study plan."
    )


def calculate_ats_score(resume_text, skills):
    text = resume_text.lower()
    words = re.findall(r"\w+", text)

    skills_score = min(len(skills) * 4, 35)

    project_keywords = [
        "project",
        "projects",
        "developed",
        "built",
        "implemented",
        "designed",
        "launched",
        "created"
    ]
    projects_score = 20 if any(word in text for word in project_keywords) else 10
    if sum(text.count(word) for word in project_keywords) > 2:
        projects_score = 20

    education_keywords = [
        "b.tech",
        "btech",
        "bachelor",
        "degree",
        "university",
        "mba",
        "m.s",
        "msc",
        "phd"
    ]
    education_score = 15 if any(word in text for word in education_keywords) else 0

    experience_keywords = [
        "experience",
        "intern",
        "internship",
        "worked",
        "developer",
        "engineer",
        "analyst",
        "managed",
        "leading",
        "lead",
        "responsible"
    ]
    experience_score = 0
    if any(word in text for word in experience_keywords):
        experience_score = 10
    if sum(text.count(word) for word in experience_keywords) > 2:
        experience_score = 15

    cert_keywords = [
        "certification",
        "certificate",
        "coursera",
        "udemy",
        "aws",
        "google",
        "microsoft",
        "professional certification",
        "completed"
    ]
    certifications_score = 10 if any(word in text for word in cert_keywords) else 0

    contact_score = 0
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        contact_score += 3
    if re.search(r"\+?\d[\d\s\-]{9,}", text):
        contact_score += 2

    resume_length_score = 0
    word_count = len(words)
    if word_count >= 400:
        resume_length_score = 5
    elif word_count >= 250:
        resume_length_score = 4
    elif word_count >= 180:
        resume_length_score = 3
    else:
        resume_length_score = 1

    links_score = 0
    if "linkedin.com" in text:
        links_score += 2
    if "github.com" in text or "kaggle.com" in text or "portfolio" in text:
        links_score += 3

    summary_score = 5 if "summary" in text or "objective" in text else 0

    total_score = (
        skills_score
        + projects_score
        + education_score
        + experience_score
        + certifications_score
        + contact_score
        + resume_length_score
        + links_score
        + summary_score
    )

    return {
        "score": min(total_score, 100),
        "skills_score": skills_score,
        "projects_score": projects_score,
        "education_score": education_score,
        "experience_score": experience_score,
        "certifications_score": certifications_score,
        "contact_score": contact_score,
        "resume_length_score": resume_length_score,
        "links_score": links_score,
        "summary_score": summary_score
    }


def generate_resume_suggestions(ats_data, skills, top_missing, top_job):
    suggestions = []

    if ats_data["skills_score"] < 20:
        suggestions.append(
            "Add role-specific technical skills and keywords in a dedicated Skills section."
        )
    elif ats_data["skills_score"] < 30:
        suggestions.append(
            "Include more relevant tools and libraries from the target job description."
        )

    if ats_data["projects_score"] < 15:
        suggestions.append(
            "Include 2–3 strong projects with clear outcomes, technologies used, and your role."
        )
    elif ats_data["projects_score"] < 20:
        suggestions.append(
            "Turn one project into a more detailed case study with metrics and impact."
        )

    if ats_data["experience_score"] < 10:
        suggestions.append(
            "Add internships, freelance work, or class projects to demonstrate practical experience."
        )
    elif ats_data["experience_score"] < 15:
        suggestions.append(
            "Use action verbs and quantify accomplishments in your experience bullets."
        )

    if ats_data["links_score"] == 0:
        suggestions.append(
            "Add your LinkedIn and GitHub or portfolio links to strengthen your profile."
        )
    elif ats_data["links_score"] < 5:
        suggestions.append(
            "Add a portfolio or Kaggle link if you have one, in addition to GitHub/LinkedIn."
        )

    if ats_data["contact_score"] < 5:
        suggestions.append(
            "Include a phone number, professional email, and city/location on your resume."
        )

    if ats_data["resume_length_score"] < 4:
        suggestions.append(
            "Expand your project and experience descriptions to show the full scope of your work."
        )

    if ats_data["certifications_score"] == 0:
        suggestions.append(
            "Add relevant certifications, training, or professional courses."
        )

    if ats_data["education_score"] == 0:
        suggestions.append(
            "Add a clear Education section with degree, institution, and graduation year."
        )

    if ats_data["summary_score"] == 0:
        suggestions.append(
            "Add a short professional summary or objective at the top to highlight your career focus."
        )

    if top_job == "Data Analyst":
        if "tableau" not in skills and "power bi" not in skills:
            suggestions.append(
                "Mention Tableau or Power BI skills to improve your fit for Data Analyst roles."
            )
        if "excel" in skills:
            suggestions.append(
                "Highlight advanced Excel skills like Pivot Tables, Power Query, and VLOOKUP."
            )

    elif top_job in ["Junior Data Scientist", "Data Scientist"]:
        if "numpy" not in skills:
            suggestions.append(
                "Add NumPy to your technical skills, as it is essential for data science roles."
            )
        if "scikit-learn" not in skills:
            suggestions.append(
                "Mention Scikit-Learn and the ML algorithms you have used."
            )
        suggestions.append(
            "Quantify your machine learning work with metrics like accuracy, F1-score, or RMSE."
        )

    elif top_job == "Business Analyst":
        suggestions.append(
            "Highlight business impact, stakeholder communication, and dashboard work."
        )

    elif top_job == "Product Analyst":
        suggestions.append(
            "Highlight SQL analytics, A/B testing, and product metrics in your resume."
        )

    if top_missing:
        top_missing_refined = [skill for skill in top_missing if skill and skill.lower() != "none"]
        if top_missing_refined:
            suggestions.append(
                f"Consider learning {', '.join(top_missing_refined[:3])} to improve your ATS match."
            )

    if len(suggestions) == 0:
        suggestions.append(
            "Your resume looks strong; focus on tailoring it to each job you apply for."
        )

    return suggestions


def create_pdf_report(
    ats_score,
    skills,
    results,
    missing_skills,
    roadmap,
    projects
):
    pdf_file = f"career_report_{uuid.uuid4().hex[:8]}.pdf"
    doc = SimpleDocTemplate(pdf_file)
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("AI Career Report", styles["Title"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"ATS Score: {ats_score}/100", styles["Heading2"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Detected Skills:", styles["Heading2"]))
    content.append(Paragraph(
        ", ".join(skills),
        styles["BodyText"]
    ))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Top Job Recommendations:", styles["Heading2"]))
    for _, row in results.head(5).iterrows():
        content.append(Paragraph(
            f"{row['Job Title']} ({row['overall_score']:.2f}%)",
            styles["BodyText"]
        ))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Missing Skills", styles["Heading2"]))
    for skill in missing_skills:
        content.append(Paragraph(f"• {skill}", styles["BodyText"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Learning Roadmap", styles["Heading2"]))
    for step in roadmap:
        content.append(Paragraph(f"• {step}", styles["BodyText"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Recommended Projects", styles["Heading2"]))
    for project in projects:
        content.append(Paragraph(f"• {project}", styles["BodyText"]))
    doc.build(content)
    return pdf_file


def extract_text(file):
    text = ""
    pdf = PyPDF2.PdfReader(file)
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text


def main():
    st.set_page_config(
        page_title="AI Job Recommender",
        layout="wide"
    )

    if "skills_only" not in st.session_state:
        st.session_state["skills_only"] = []

    if "results" not in st.session_state:
        st.session_state["results"] = None


    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    if "ats_score" not in st.session_state:
        st.session_state["ats_score"] = 0

    if "resume_text" not in st.session_state:
        st.session_state["resume_text"] = ""


    # -----------------------------
    # DARK THEME UI
    # -----------------------------
    st.markdown("""
    <style>

    .stApp {
        background-color: #0e1117;
        color: white;
    }

    h1, h2, h3, h4 {
        color: white;
    }

    .stFileUploader {
        background-color: #161b22;
        border-radius: 10px;
        padding: 10px;
    }

    div.stButton > button {
        background-color: #00b894;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
    }

    div.stButton > button:hover {
        background-color: #00a383;
    }

    </style>
    """, unsafe_allow_html=True)

    # -----------------------------
    # TITLE
    # -----------------------------
    st.title("💼 AI-Powered Job Recommendation System")
    if "user" not in st.session_state:
        st.session_state.user = None


    if st.session_state.user is None:

        auth_mode = st.radio(
            "Choose",
            ["Login", "Signup"],
            horizontal=True
        )

        if auth_mode == "Signup":

            st.subheader("📝 Create Account")

            signup_name = st.text_input(
                "Name"
            )

            signup_email = st.text_input(
                "Email"
            )

            signup_password = st.text_input(
                "Password",
                type="password"
            )

            if st.button("Create Account"):

                create_user(
                    signup_name,
                    signup_email,
                    signup_password
                )

                st.success(
                    "Account created successfully"
                )

        else:

            st.subheader("🔐 Login")

            login_email = st.text_input(
                "Email"
            )

            login_password = st.text_input(
                "Password",
                type="password"
            )

            if st.button("Login"):

                user = login_user(
                    login_email,
                    login_password
                )

                if user:

                    st.session_state.user = {
                        "id": user[0],
                        "name": user[1]
                    }

                    st.rerun()

                else:

                    st.error(
                        "Invalid email or password"
                    )

        st.stop()

    # -----------------------------
    # SIDEBAR
    # -----------------------------
    reports_page = False
    st.sidebar.title("⚡ AI Career Dashboard")
    if st.session_state.user:

        st.sidebar.markdown(
            f"### 👋 {st.session_state.user['name']}"
        )

        reports_page = st.sidebar.button(
            "📂 My Reports"
        )

        if st.sidebar.button("🚪 Logout"):

            st.session_state.user = None

            st.rerun()


    if reports_page:

        reports = get_reports(
            st.session_state.user["id"]
        )

        st.title("📂 My Previous Reports")

        if reports:

            reports_df = pd.DataFrame(
                reports,
                columns=[
                    "Resume",
                    "ATS Score",
                    "Top Job",
                    "Date"
                ]
            )

            st.dataframe(
                reports_df,
                use_container_width=True
            )

        else:

            st.info(
                "No reports found."
            )

        st.stop()



    st.sidebar.markdown("""
    ### 📊 Features:
    - Resume Analysis
    - Skill Detection
    - Job Matching
    - Missing Skills Report
    - Learning Roadmap
    - Project Suggestions
    """)

    st.markdown(f"""
    <div style="
    background-color:#161b22;
    padding:15px;
    border-radius:12px;
    border:1px solid #30363d;">

    <h3>👋 Welcome, {st.session_state.user['name']}</h3>

    <p>
    Upload your resume and get AI-powered job recommendations.
    </p>

    </div>
    """, unsafe_allow_html=True)

    # Skill extraction is handled in skills_utils.py.

    skills_only = st.session_state.get("skills_only", [])
    ats_data = st.session_state.get("ats_data", None)
    top_missing = st.session_state.get("top_missing", [])
    top_roadmap = st.session_state.get("top_roadmap", {"roadmap": [], "projects": []})
    results = st.session_state.get("results")
    ats_score = st.session_state.get("ats_score", 0)
    resume_text = st.session_state.get("resume_text", "")


    # PDF TEXT EXTRACTION
    # -----------------------------

    # -----------------------------
    # FILE UPLOAD
    # -----------------------------
    uploaded_file = st.file_uploader(
        "📄 Upload Resume (PDF)",
        type=["pdf"]
    )
    if uploaded_file:
        st.session_state.report_saved = False
    # -----------------------------
    # MAIN LOGIC
    # -----------------------------
    if st.button("Analyze Resume"):
        if uploaded_file is None:
            st.error("Please upload a PDF resume.")
            st.stop()

        resume_text = extract_text(uploaded_file)
        st.session_state["resume_text"] = resume_text

        
        st.subheader("📄 Extracted Resume Text")
        with st.expander("View Resume Content"):
            st.write(resume_text)

       
        skills_only = extract_skills_from_utils(resume_text)

        ats_data = calculate_ats_score(
        resume_text,
        skills_only
    )
    

        ats_score = ats_data["score"]
        st.session_state["ats_score"] = ats_score

        st.session_state["skills_only"] = skills_only
        st.session_state["ats_data"] = ats_data

        # Get recommendations using local recommender
        try:
            recs = recommend_jobs(resume_text)
            results = pd.DataFrame(recs)
            st.session_state["results"] = results
        except Exception as e:
            st.error(f"Failed to get recommendations: {e}")
            st.stop()

        if results is None or results.empty:
            st.warning("No job recommendations found.")
            st.stop()

        # Metrics
        col1, col2 = st.columns(2)
        col1.metric("🧠 Skills Detected", len(skills_only))
        col2.metric("🎯 Jobs Matched", len(results))

        st.subheader("📊 ATS Resume Score")

        if ats_score >= 80:
            score_color = "#00b894"
            score_label = "Excellent"
        elif ats_score >= 60:
            score_color = "#fdcb6e"
            score_label = "Good"
        else:
            score_color = "#ff7675"
            score_label = "Needs Improvement"

        st.markdown(f"""
<div style="background-color:#161b22; padding:20px; border-radius:12px; border:1px solid #30363d;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:28px; font-weight:bold; color:{score_color};">{ats_score}/100</span>
        <span style="background-color:{score_color}; color:#0e1117; padding:4px 12px; border-radius:20px; font-weight:bold; font-size:13px;">{score_label}</span>
    </div>
    <div style="background-color:#30363d; border-radius:10px; height:12px; margin-top:12px; overflow:hidden;">
        <div style="background-color:{score_color}; width:{ats_score}%; height:100%; border-radius:10px;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

        ats_data = st.session_state.get("ats_data")

        ats_score = st.session_state.get("ats_score", 0)

        if ats_data and results is not None and not results.empty:

            st.markdown("### 📋 ATS Breakdown")

            st.write(
                f"✅ Skills: {ats_data['skills_score']}/35"
            )

            st.write(
                f"✅ Projects: {ats_data['projects_score']}/20"
            )

            st.write(
                f"✅ Education: {ats_data['education_score']}/15"
            )

            st.write(
                f"✅ Experience: {ats_data['experience_score']}/15"
            )

            st.write(
                f"✅ Certifications: {ats_data['certifications_score']}/10"
            )

            st.write(
                f"✅ Contact Info: {ats_data['contact_score']}/5"
            )

            st.write(
                f"✅ Resume Length: {ats_data['resume_length_score']}/5"
            )

            st.write(
                f"✅ LinkedIn/GitHub: {ats_data['links_score']}/5"
            )

            st.write(
                f"✅ Summary/Objective: {ats_data.get('summary_score', 0)}/5"
            )

            if ats_score >= 80:
                st.success("Excellent Resume")
            elif ats_score >= 60:
                st.info("Good Resume")
            else:
                st.warning("Needs Improvement")

            top_job = results.iloc[0]["Job Title"]
            st.session_state["top_job"] = top_job

            raw_missing = results.iloc[0].get("missing_skills", "")

            if isinstance(raw_missing, list):
                top_missing = [str(s).strip() for s in raw_missing if str(s).strip() and str(s).strip().lower() != "none"]
            else:
                top_missing = [
                    s.strip()
                    for s in str(raw_missing).split(",")
                    if s.strip() and s.strip().lower() != "none"
                ]

            st.session_state["top_missing"] = top_missing

            resume_suggestions = generate_resume_suggestions_gemini(
                top_job,
                skills_only,
                top_missing,
                ats_data
            )

            ai_insight = generate_ai_insights(
                resume_text,
                top_job,
                skills_only,
                top_missing
            )

            st.markdown("### 🧠 AI Career Insight (Top Job)")
            st.write(ai_insight)

            suggestions = generate_resume_suggestions(
                ats_data,
                skills_only,
                top_missing,
                top_job
            )

            st.markdown("### 📈 Resume Improvement Suggestions")

            for suggestion in suggestions:
                st.markdown(f"- {suggestion}")

            top_roadmap = generate_roadmap(top_missing, top_job)
            st.session_state["top_roadmap"] = top_roadmap

    # Retrieve session state for display sections
    ats_score = st.session_state.get("ats_score", 0)
    skills_only = st.session_state.get("skills_only", [])
    results = st.session_state.get("results", pd.DataFrame())
    top_missing = st.session_state.get("top_missing", [])
    top_roadmap = st.session_state.get(
        "top_roadmap",
        {"roadmap": [], "projects": []}
    )
    top_job = st.session_state.get("top_job", "")

    if "report_saved" not in st.session_state:
        st.session_state.report_saved = False

    if (
        uploaded_file is not None
        and not st.session_state.report_saved
        and ats_score > 0
    ):
        save_report(
            st.session_state.user["id"],
            uploaded_file.name,
            ats_score,
            top_job
        )
        st.session_state.report_saved = True

    if results is None or results.empty:
        st.stop()

    pdf_path = create_pdf_report(
        ats_score,
        skills_only,
        results,
        top_missing,
        top_roadmap["roadmap"],
        top_roadmap["projects"]
    )

    with open(pdf_path, "rb") as pdf:
        st.download_button(
            label="📥 Download Career Report",
            data=pdf,
            file_name="career_report.pdf",
            mime="application/pdf"
        )

    # DETECTED SKILLS
    st.subheader("🧠 Detected Skills")

    if skills_only:
        cols = st.columns(
            min(len(skills_only), 6)
        )

        for i, skill in enumerate(
            skills_only
        ):
            cols[
                i % len(cols)
            ].markdown(
                f"🟢 {skill}"
            )
    else:
        st.warning(
            "No skills detected."
        )

    # JOB RECOMMENDATIONS
    st.subheader(
        "🎯 Top Job Recommendations"
    )

    if results is None or results.empty:
        st.warning("No job recommendations available.")
        st.stop()

    for _, row in results.head(5).iterrows():
        st.markdown(f"""
            <div style="
            background-color:#161b22;
            padding:20px;
            border-radius:15px;
            border:1px solid #30363d;
            margin-bottom:15px;">
            """, unsafe_allow_html=True)

        st.markdown(
            f"### 💼 {row['Job Title']}"
        )

        st.markdown(
            f"🟢 Skill Match: {row['skill_score']:.2f}%"
        )

        st.markdown(
            f"🟢 Resume Match: {row['resume_score']:.2f}%"
        )

        st.markdown(
            f"🟢 Overall Match: {row['overall_score']:.2f}%"
        )

        st.progress(
            min(
                int(row['overall_score']),
                100
            )
        )

        st.markdown(
            "#### 🔍 Missing Skills"
        )

        missing = row.get(
            "missing_skills",
            ""
        )

        if isinstance(missing, list):
            skills = [str(s).strip() for s in missing if str(s).strip() and str(s).strip().lower() != "none"]
        else:
            skills = [
                s.strip()
                for s in str(missing).split(",")
                if s.strip()
                and s.strip().lower() != "none"
            ]

        if skills:
            categorized = categorize_missing_skills(
                skills
            )

            if categorized["high"]:
                st.markdown(
                    "🔥 High Priority"
                )
                for skill in categorized["high"]:
                    st.markdown(
                        f"- {skill}"
                    )

            if categorized["medium"]:
                st.markdown(
                    "🟡 Medium Priority"
                )
                for skill in categorized["medium"]:
                    st.markdown(
                        f"- {skill}"
                    )

            if categorized["low"]:
                st.markdown(
                    "🟢 Nice To Have"
                )
                for skill in categorized["low"]:
                    st.markdown(
                        f"- {skill}"
                    )
        else:
            st.info(
                "No explicit missing skills were detected for this role."
            )

        roadmap_data = generate_roadmap(
            skills,
            row["Job Title"]
        )

        st.markdown(
            "#### 🛣️ Learning Roadmap"
        )

        for i, step in enumerate(
            roadmap_data["roadmap"],
            start=1
        ):
            st.markdown(
                f"{i}. {step}"
            )

        st.markdown(
            "#### 💡 Recommended Projects"
        )

        for i, project in enumerate(
            roadmap_data["projects"],
            start=1
        ):
            st.markdown(
                f"{i}. {project}"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )



    # CHATBOT SECTION
    st.markdown("---")
    st.subheader("🤖 Career Chatbot")

    skills = st.session_state.get("skills_only", [])
    results = st.session_state.get("results", None)

    user_query = st.text_input("Ask your career question:")

    if user_query:
        if results is not None and len(results) > 0:
            st.session_state["chat_history"].append(
                {
                    "role": "user",
                    "content": user_query
                }
            )

            try:
                response = requests.post(
                    "http://127.0.0.1:8000/chat",
                    json={
                        "message": user_query,
                        "skills": skills,
                        "job": results.iloc[0]["Job Title"],
                        "history": st.session_state["chat_history"]
                    },
                    timeout=5,
                )

                if response.status_code == 200:
                    ai_reply = response.json().get("response", "No response received.")
                else:
                    ai_reply = build_fallback_chat_reply(
                        user_query,
                        skills,
                        results.iloc[0]["Job Title"] if results is not None and len(results) > 0 else None,
                    )
            except requests.exceptions.RequestException:
                ai_reply = build_fallback_chat_reply(
                    user_query,
                    skills,
                    results.iloc[0]["Job Title"] if results is not None and len(results) > 0 else None,
                )

            st.session_state["chat_history"].append(
                {
                    "role": "assistant",
                    "content": ai_reply
                }
            )

            st.success(ai_reply)
        else:
            st.warning("Please analyze resume first.")

    st.markdown("---")
    st.subheader("💬 Chat History")

    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(
                f"🧑 **You:** {msg['content']}"
            )
        else:
            st.markdown(
                f"🤖 **AI:** {msg['content']}"
            )

if __name__ == "__main__":
    main()
