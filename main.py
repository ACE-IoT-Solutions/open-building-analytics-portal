import inspect
import typing
from io import BytesIO

import pandas as pd
import streamlit as st

import faults
import reports

fault_map = {x[0]: x[1] for x in inspect.getmembers(faults, inspect.isclass)}
report_map = {x[0]: x[1] for x in inspect.getmembers(reports, inspect.isclass)}

input_map = {
    float: st.number_input,
    int: st.number_input,
    str: st.text_input,
    bool: st.checkbox,
}

rule_to_check = st.selectbox("What rule would you like to check?", fault_map.keys())
inputs = inspect.signature(fault_map[rule_to_check])
samples = st.file_uploader("Upload a CSV file", type="csv")

column_mappings = {}
parameters = {}
if samples is not None:
    dataframe = pd.read_csv(samples)
    st.write(dataframe)
    for input in (input for input in inputs.parameters if input.endswith("_col")):
        column_mappings[input] = st.selectbox(
            f"Input for {rule_to_check} - {input}", [col for col in dataframe.columns]
        )
        st.write(column_mappings[input])
    for input, p in {
        input: p for input, p in inputs.parameters.items() if not input.endswith("_col")
    }.items():
        parameters[input] = input_map[p.annotation](
            f"Input for {rule_to_check} - {input}"
        )
        st.write(parameters[input])

    if st.button("Run Analysis"):
        res = fault_map[rule_to_check](**column_mappings, **parameters).apply(dataframe)
        st.write(res)
    report_name = st.text_input("Report Name")
    if st.button("Run Report"):
        res = fault_map[rule_to_check](**column_mappings, **parameters).apply(dataframe)
        report_def = report_map[f'{rule_to_check.replace("Condition", "Code")}Report']
        filtered_args = {key: value for key, value in column_mappings.items() if key in inspect.signature(report_def).parameters}
        report = report_def(**filtered_args).create_report(report_name, res)
        download_file = BytesIO()
        report.save(download_file)
        download_file.seek(0)
        st.write(
            st.download_button(
                "DownloadReport",
                download_file,
                f"{report_name}.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        )

        st.write(report.report)
