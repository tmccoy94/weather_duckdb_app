import duckdb
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")

st.set_page_config(page_title="DuckDB Viewer", layout="wide")

st.title("🦆 DuckDB Viewer")

# Pick your file
db_path = st.text_input("Path to DuckDB file", f"{DB_NAME}.duckdb")

if db_path:
    try:
        con = duckdb.connect(db_path, read_only=True)

        # Sidebar navigation
        page = st.sidebar.radio("Navigate", ["Browse Tables", "Schema"])

        if page == "Browse Tables":
            # Show tables
            tables = con.execute("SHOW TABLES").fetchall()
            table_names = [t[0] for t in tables]

            st.sidebar.header("Tables")
            table = st.sidebar.selectbox("Select a table", table_names)

            if table:
                st.subheader(f"Preview: `{table}`")
                query = f"SELECT * FROM {table} LIMIT 100"
                df = con.execute(query).df()
                st.dataframe(df, width='stretch')

                # Ad-hoc queries
                st.subheader("Run SQL")
                sql = st.text_area("SQL query", query, height=100)
                if st.button("Run query"):
                    try:
                        result = con.execute(sql).df()
                        st.dataframe(result, width='stretch')
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif page == "Schema":
            st.subheader("Database Schema")

            # Get tables + columns
            schema_df = con.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema='main'
                ORDER BY table_name, ordinal_position
            """).df()

            for table in schema_df["table_name"].unique():
                st.markdown(f"### 📋 {table}")
                st.dataframe(
                    schema_df[schema_df["table_name"] == table][["column_name", "data_type"]],
                    width='stretch'
                )

            # Inferred relationships
            st.subheader("Inferred Relationships")
            try:
                relationships = []
                tables = schema_df["table_name"].unique()
                for t1 in tables:
                    cols1 = schema_df[schema_df["table_name"] == t1]["column_name"].tolist()
                    for t2 in tables:
                        if t1 != t2:
                            cols2 = schema_df[schema_df["table_name"] == t2]["column_name"].tolist()
                            common = set(cols1).intersection(set(cols2))
                            for c in common:
                                relationships.append((t1, c, t2, c))

                if relationships:
                    rel_df = pd.DataFrame(
                        relationships,
                        columns=["Table A", "Key A", "Table B", "Key B"]
                    )
                    st.dataframe(rel_df, width='stretch')
                else:
                    st.info("No obvious relationships inferred.")
            except Exception as e:
                st.warning(f"Could not infer relationships: {e}")

        con.close()

    except Exception as e:
        st.error(f"Could not open database: {e}")

