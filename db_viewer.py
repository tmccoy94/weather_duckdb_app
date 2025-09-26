import duckdb
import streamlit as st
import pandas as pd
import re
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
            st.sidebar.header("Database Objects")

            # Tables
            tables = con.execute("SHOW TABLES").fetchall()
            table_names = [t[0] for t in tables]

            with st.sidebar.expander(f"📂 Tables ({len(table_names)})", expanded=True):
                table = st.selectbox("Select table", table_names, label_visibility="collapsed")

            # Views
            views = con.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema='main' AND table_type='VIEW'
            """).fetchall()
            view_names = [v[0] for v in views]

            with st.sidebar.expander(f"📂 Views ({len(view_names)})", expanded=False):
                view = st.selectbox("Select view", ["<none>"] + view_names, label_visibility="collapsed")

            # Main preview area
            if table:
                st.subheader(f"Preview: `{table}`")
                query = f"SELECT * FROM {table} LIMIT 100"
                df = con.execute(query).df()
                st.dataframe(df, use_container_width=True)

            if view and view != "<none>":
                st.subheader(f"Preview View: `{view}`")
                query = f"SELECT * FROM {view} LIMIT 100"
                df = con.execute(query).df()
                st.dataframe(df, use_container_width=True)

            # --- SQL Query Box (always available) ---
            st.subheader("Run SQL")
            default_sql = f"SELECT * FROM {table or view} LIMIT 100" if (table or view) else "SELECT 1"
            sql = st.text_area("SQL query", default_sql, height=100)
            if st.button("Run query"):
                try:
                    result = con.execute(sql).df()
                    st.dataframe(result, use_container_width=True)
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
            
            def sanitize_name(name: str) -> str:
                """Make column names safe for Graphviz port labels."""
                return re.sub(r'\W|^(?=\d)', '_', name)

            # # ER diagram - add later, will need some troubleshooting lol
            # st.subheader("Entity-Relationship Diagram")

            # dot = """
            # digraph G {
            #     rankdir=LR;
            #     splines=ortho;
            #     nodesep=0.6;
            #     node [shape=plaintext, fontname=Helvetica];
            # """

            # for table in schema_df["table_name"].unique():
            #     cols = schema_df[schema_df["table_name"] == table][["column_name", "data_type"]]

            #     # Build table node with column ports
            #     label = f'<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
            #     label += f'<TR><TD BGCOLOR="lightblue" COLSPAN="2"><B>{table}</B></TD></TR>'
            #     for _, row in cols.iterrows():
            #         col_name = row["column_name"]
            #         port = sanitize_name(col_name)

            #         # Highlight candidate keys
            #         if col_name.lower() in ("id", f"{table}_id"):
            #             color = "palegreen"
            #         elif col_name.lower().endswith("_id"):
            #             color = "lightyellow"
            #         else:
            #             color = "white"

            #         label += f'<TR><TD PORT="{port}" BGCOLOR="{color}">{col_name}</TD><TD>{row["data_type"]}</TD></TR>'
            #     label += "</TABLE>>"

            #     dot += f'{table} [label={label}];\n'

            # # Draw arrows using ports
            # for (t1, c1, t2, c2) in relationships:
            #     dot += f'{t1}:{sanitize_name(c1)} -> {t2}:{sanitize_name(c2)} [arrowhead=normal, arrowsize=0.7];\n'

            # dot += "}"

            # st.graphviz_chart(dot, use_container_width=True)

        con.close()

    except Exception as e:
        st.error(f"{e}")

