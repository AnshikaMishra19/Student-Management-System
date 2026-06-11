import streamlit as st
import pandas as pd
import sqlite3

# ---------- DATABASE ----------
conn = sqlite3.connect("students.db", check_same_thread=False)
c = conn.cursor()

# Create table if not exists
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    name TEXT PRIMARY KEY,
    marks INTEGER
)
""")
conn.commit()
# ---------- DB FUNCTIONS ----------

def add_student_db(name, marks):
    with conn:
        conn.execute("INSERT OR REPLACE INTO students VALUES (?, ?)", (name, marks))

def get_all_students():
    c.execute("SELECT * FROM students")
    return dict(c.fetchall())

def delete_student_db(name):
    c.execute("DELETE FROM students WHERE name=?", (name,))
    conn.commit()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Student Dashboard", layout="wide")

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
.main {
    background-color: grey;
}

h1 {
    color: white;
    text-align: center;
}

.card {
    padding: 20px;
    border-radius: 15px;
    background: linear-gradient(135deg, #6dd5ed, #2193b0);
    color: white;
    text-align: center;
    font-size: 18px;
}

.metric-card {
    padding: 15px;
    border-radius: 10px;
    background-color: #ffffff;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    text-align: center;
}

.success-box {
    background-color: #d4edda;
    padding: 10px;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ---------- TITLE ----------
st.markdown("<h1>Student Management System</h1>", unsafe_allow_html=True)

# ---------- SESSION ----------
if "students" not in st.session_state:
    st.session_state.students = get_all_students()
# ---------- SIDEBAR ----------
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Student", "Manage Students", "Analytics", "Reports", "Review"]
)

# ---------- DASHBOARD ----------
if menu == "Dashboard":
    st.subheader("Dashboard Overview")

    total = len(st.session_state.students)

    if total > 0:
        marks = list(st.session_state.students.values())
        avg = sum(marks) / total
        high = max(marks)
        low = min(marks)
    else:
        avg = high = low = 0

    # ---------- KPI CARDS ----------
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"<div class='card'><br>Total Students<br>{total}</div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><br>Average Marks<br>{avg:.2f}</div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='card'><br>Highest<br>{high}</div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='card'><br>Lowest<br>{low}</div>", unsafe_allow_html=True)
    if total > 0:
        df = pd.DataFrame(
            st.session_state.students.items(),
            columns=["Name", "Marks"]
        )

        # ---------- GRADE FUNCTION ----------
        def grade(m):
            return "A" if m >= 90 else "B" if m >= 80 else "C" if m >= 70 else "D" if m >= 60 else "F"

        df["Grade"] = df["Marks"].apply(grade)

        st.divider()

        # ---------- PERFORMANCE STATUS ----------
        st.subheader("Class Performance Status")

        if avg >= 80:
            st.success("Excellent Class Performance")
        elif avg >= 60:
            st.info("Average Performance")
        else:
            st.warning("Needs Improvement")

        st.divider()

        # ---------- CHARTS ----------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Marks Overview")
            st.area_chart(df.set_index("Name")["Marks"])

        with col2:
            st.subheader("Grade Distribution")
            st.bar_chart(df["Grade"].value_counts())

        st.divider()

        # ---------- TOP & LOW ----------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top Performers")
            top_df = df.sort_values(by="Marks", ascending=False).head(5)
            st.dataframe(top_df, use_container_width=True)

        with col2:
            st.subheader("Low Performers")
            low_df = df.sort_values(by="Marks").head(5)
            st.dataframe(low_df, use_container_width=True)

        st.divider()

        # ---------- QUICK INSIGHTS ----------
        st.subheader("Insights")

        high_count = len(df[df["Marks"] >= 85])
        low_count = len(df[df["Marks"] < 60])

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Top Performers", high_count)
        with col2:
            st.metric("Students Below Average", low_count)

        if low_count > high_count:
            st.warning("More students need improvement than excelling.")
        else:
            st.success("Good number of Top Performers!")

        st.divider()

        # ---------- RECENT ACTIVITY ----------
        st.subheader("Recent Entries")

        recent_df = df.tail(5)
        st.table(recent_df)

        # ---------- SEARCH QUICK VIEW ----------
        st.subheader("Quick Student Lookup")

        search = st.text_input("Enter student name")

        if search:
            result = df[df["Name"].str.contains(search, case=False)]
            if not result.empty:
                st.success("Student Found")
                st.dataframe(result)
            else:
                st.error("No matching student")

# ---------- ADD STUDENT ----------
elif menu == "Add Student":
    st.subheader("Add Student")

    with st.expander("Enter Details", expanded=True):
        name = st.text_input("Name")
        marks = st.slider("Marks", 0, 100)

        if st.button("Add Student"):
            if name:
                add_student_db(name, marks)
                st.session_state.students = get_all_students()
                st.success("Added Successfully!")
            elif not name.strip():
                st.warning("Name cannot be empty")
            elif not name.replace(" ", "").isalpha():
                st.warning("Name must contain only letters")
            else:
                add_student_db(name.strip(), marks)

# ---------- MANAGE ----------
elif menu == "Manage Students":
    st.subheader("Manage Students")

    if not st.session_state.students:
        st.info("No data found")
    else:
        df = pd.DataFrame(st.session_state.students.items(), columns=["Name", "Marks"])

        tab1, tab2 = st.tabs(["View", "Update/Delete"])

        with tab1:
            search = st.text_input("Search")
            if search:
                df = df[df["Name"].str.contains(search, case=False)]
            st.dataframe(df, use_container_width=True)

        with tab2:
            name = st.selectbox("Select Student", df["Name"])

            new_marks = st.slider("Marks", 0, 100,
                                  st.session_state.students[name])

            col1, col2 = st.columns(2)

            if col1.button("Update"):
                add_student_db(name, new_marks) 
                st.session_state.students = get_all_students()
                st.success("Updated permanently!")

            if col2.button("Delete"):
                delete_student_db(name) 
                st.session_state.students = get_all_students()
                st.warning("Deleted permanently!")

# ---------- ANALYTICS ----------
elif menu == "Analytics":
    st.subheader("Analytics Dashboard")

    if not st.session_state.students:
        st.info("No data available")
    else:
        df = pd.DataFrame(
            st.session_state.students.items(),
            columns=["Name", "Marks"]
        )

        # ---------- Grade Function ----------
        def grade(m):
            return "A" if m >= 90 else "B" if m >= 80 else "C" if m >= 70 else "D" if m >= 60 else "F"

        df["Grade"] = df["Marks"].apply(grade)

        # ---------- Filters ----------
        st.sidebar.subheader("Analytics Filter")
        min_marks = st.sidebar.slider("Minimum Marks", 0, 100, 0)
        max_marks = st.sidebar.slider("Maximum Marks", 0, 100, 100)

        filtered_df = df[(df["Marks"] >= min_marks) & (df["Marks"] <= max_marks)]

        # ---------- Key Metrics ----------
        st.subheader("Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Students", len(filtered_df))
        col2.metric("Average", f"{filtered_df['Marks'].mean():.2f}")
        col3.metric("Median", f"{filtered_df['Marks'].median():.2f}")
        col4.metric("Max", filtered_df["Marks"].max())
        col5.metric("Min", filtered_df["Marks"].min())

        st.divider()

        # ---------- Charts ----------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Grade Distribution")
            grade_counts = filtered_df["Grade"].value_counts()
            st.bar_chart(grade_counts)

            # Percentage breakdown
            st.write("### Grade Percentage")
            percent = (grade_counts / len(filtered_df)) * 100
            st.write(percent.round(2).astype(str) + " %")

        with col2:
            st.subheader("Marks Analysis")
            st.line_chart(filtered_df.set_index("Name")["Marks"])

        st.divider()

        # ---------- Performance Groups ----------
        st.subheader("Performance Groups")

        high = filtered_df[filtered_df["Marks"] >= 85]
        avg = filtered_df[(filtered_df["Marks"] >= 60) & (filtered_df["Marks"] < 85)]
        low = filtered_df[filtered_df["Marks"] < 60]

        col1, col2, col3 = st.columns(3)

        col1.success(f"High Performers: {len(high)}")
        col2.info(f"Average Performers: {len(avg)}")
        col3.error(f"Low Performers: {len(low)}")

        st.divider()

        # ---------- Top & Bottom ----------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top 5 Students")
            st.table(filtered_df.sort_values(by="Marks", ascending=False).head(5))

        with col2:
            st.subheader("Bottom 5 Students")
            st.table(filtered_df.sort_values(by="Marks").head(5))

        st.divider()

        # ---------- Insights ----------
        st.subheader("Insights")

        avg_marks = filtered_df["Marks"].mean()

        if avg_marks >= 80:
            st.success("Overall class performance is excellent.")
        elif avg_marks >= 60:
            st.info("Class performance is moderate.")
        else:
            st.warning("Class performance needs improvement.")

        if len(low) > len(high):
            st.warning("More students are struggling than excelling.")
        else:
            st.success("Good number of high performers!")

        st.divider()

        # ---------- Data Table ----------
        st.subheader("Full Data")
        st.dataframe(filtered_df, use_container_width=True)

# ---------- REPORT ----------
elif menu == "Reports":
    st.subheader("Reports Dashboard")

    if not st.session_state.students:
        st.info("No data available.")
    else:
        df = pd.DataFrame(
            st.session_state.students.items(),
            columns=["Name", "Marks"]
        )

        # ---------- Grade Function ----------
        def get_grade(m):
            return "A" if m >= 90 else "B" if m >= 80 else "C" if m >= 70 else "D" if m >= 60 else "F"

        df["Grade"] = df["Marks"].apply(get_grade)

        # ---------- Filters ----------
        st.sidebar.subheader("Filter Report")
        grade_filter = st.sidebar.multiselect(
            "Select Grades",
            options=df["Grade"].unique(),
            default=df["Grade"].unique()
        )

        filtered_df = df[df["Grade"].isin(grade_filter)]

        # ---------- Summary Cards ----------
        st.subheader("Summary")

        total = len(filtered_df)
        avg = filtered_df["Marks"].mean() if total > 0 else 0
        highest = filtered_df["Marks"].max() if total > 0 else 0
        lowest = filtered_df["Marks"].min() if total > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Students", total)
        col2.metric("Average Marks", f"{avg:.2f}")
        col3.metric("Highest", highest)
        col4.metric("Lowest", lowest)

        st.divider()

        # ---------- Data Table ----------
        st.subheader("Detailed Report")
        st.dataframe(filtered_df, use_container_width=True)

        # ---------- Charts ----------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Grade Distribution")
            st.bar_chart(filtered_df["Grade"].value_counts())

        with col2:
            st.subheader("Marks Distribution")
            st.line_chart(filtered_df.set_index("Name")["Marks"])

        st.divider()

        # ---------- Top & Low Performers ----------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top Performers")
            top = filtered_df.sort_values(by="Marks", ascending=False).head(5)
            st.table(top)

        with col2:
            st.subheader("Low Performers")
            low = filtered_df.sort_values(by="Marks").head(5)
            st.table(low)

        st.divider()

        # ---------- Download ----------
        st.subheader("Download Report")
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Filtered Report",
            csv,
            "filtered_report.csv",
            mime="text/csv"
        )

# ---------- REVIEW ----------
elif menu == "Review":
    st.subheader("Student Performance Review")

    if not st.session_state.students:
        st.info("No students available for review.")
    else:
        df = pd.DataFrame(
            list(st.session_state.students.items()),
            columns=["Name", "Marks"]
        )

        # Select student
        selected_student = st.selectbox("Select Student", df["Name"])

        marks = st.session_state.students[selected_student]

        # Grade logic
        if marks >= 90:
            student_grade = "A"
            remark = "Excellent Performance"
            color = "green"
            suggestion = """You are performing exceptionally well and consistently achieving high marks. 
            Your understanding of concepts is strong and clearly reflected in your performance. 
            Continue maintaining this level of dedication and accuracy. To further enhance your skills, 
            you are encouraged to take on more advanced problems and challenging tasks that will deepen your
            knowledge and push your abilities to the next level."""
        elif marks >= 80:
            student_grade = "B"
            remark = "Very Good"
            color = "blue"
            suggestion = """You are performing very well and have a good understanding of the subject.
            Your current results show strong effort and capability. To reach the highest level (Grade A), 
            focus on maintaining consistency in your performance across all topics. 
            Regular practice, attention to detail, and improving accuracy will help you achieve excellent results."""
        elif marks >= 70:
            student_grade = "C"
            remark = "Good"
            color = "orange"
            suggestion = """You are performing fairly well, but there are certain areas that need more attention. 
            Identify the topics where you are facing difficulty and work on strengthening those concepts.
            Regular practice, revision, and solving a variety of questions will help improve your understanding and boost your overall performance."""
        elif marks >= 60:
            student_grade = "D"
            remark = "Needs Improvement"
            color = "red"
            suggestion = """You need to strengthen your understanding of the basic concepts, 
            as they form the foundation for better performance. 
            Spend time revising fundamental topics and ensure you clearly understand them. 
            Regular practice, along with solving different types of questions, will help improve your accuracy, confidence, and overall results."""
        else:
            student_grade = "F"
            remark = "Failed"
            color = "darkred"
            suggestion = """Your current performance indicates that you need immediate improvement. 
            It is important to focus on understanding the basic concepts from the beginning. 
            You are strongly advised to seek guidance from your teacher or mentor to clarify doubts. 
            Regular revision, consistent practice, and dedicated effort will help you gradually improve your performance and build confidence."""

        # Layout
        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric("Marks", marks)
            st.metric("Grade", student_grade)

        with col2:
            st.markdown(f"### {remark}")
            st.write(f"Suggestion: {suggestion}")

        st.divider()

        # Progress bar
        st.subheader("Performance Level")
        st.progress(marks / 100)

        # Comparison
        avg_marks = df["Marks"].mean()
        st.subheader("Comparison with Class Average")

        if marks > avg_marks:
            st.success(f"Above average! (Class Avg: {avg_marks:.2f})")
        elif marks == avg_marks:
            st.info(f"Equal to average (Class Avg: {avg_marks:.2f})")
        else:
            st.warning(f"Below average (Class Avg: {avg_marks:.2f})")

        # Strength & Weakness Insight
        st.subheader("Performance Insight")

        if marks >= 85:
            st.success("Strong understanding of concepts.")
        elif marks >= 60:
            st.info("Moderate understanding. Needs improvement in some areas.")
        else:
            st.error("Weak understanding. Needs serious improvement.")

        # Expandable detailed feedback
        with st.expander("Detailed Feedback"):
            st.write(f"""
            **Student Name:** {selected_student}  
            **Marks:** {marks}  
            **Grade:** {student_grade}  

            **Teacher's Comment:**  
            {suggestion}
            """)
