import json
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen

import multiqc
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from multiqc.plots import bargraph

# Sidebar
# --- Initialize Session State --- #
if "bytes_data" not in st.session_state:
    st.session_state.bytes_data = None
if "data_source" not in st.session_state:
    st.session_state.data_source = None

input_method = None
uploaded_file = None
data_url = None
with st.sidebar:
    st.title("MultiQC Streamlit App")

    # --- Input Method Selection --- #
    input_method = st.radio(
        "Choose input method",
        ("Load from URL", "Upload File")
    )

    if input_method == "Load from URL":
        st.write("Enter the URL of a MultiQC data ZIP file.")
        # Set DATA_URL in an input
        data_url = st.text_input(
            "Demo Data URL", "https://seqera.io/examples/hi-c/data.zip"
        )
        if st.button("Fetch and Load Data"):
            if data_url:
                with st.spinner(f"Downloading from {data_url}..."):
                    try:
                        http_response = urlopen(data_url)
                        st.session_state.bytes_data = http_response.read()
                        st.session_state.data_source = f"URL: {data_url}"
                        st.success("Download successful!")
                    except Exception as e:
                        st.error(f"Error downloading from URL: {e}")
                        st.session_state.bytes_data = None
                        st.session_state.data_source = None
            else:
                st.warning("Please enter a URL.")
    elif input_method == "Upload File":
        # File uploader
        st.write("Upload a MultiQC data ZIP file to analyze.")
        uploaded_file = st.file_uploader(
            "Upload Data ZIP", type="zip", help="Upload a ZIP archive containing MultiQC data."
        )
        # Update session state immediately on upload
        if uploaded_file is not None:
            st.session_state.bytes_data = uploaded_file.getvalue()
            st.session_state.data_source = f"File: {uploaded_file.name}"

    # Set EXAMPLE_CUSTOM_DATA in an input - Keep in sidebar for editing anytime
    EXAMPLE_CUSTOM_DATA = st.text_area(
        "Custom Data (edit before generating report)",
        """{
        "sample 1": {"aligned": 23542, "not_aligned": 343},
        "sample 2": {"aligned": 1275, "not_aligned": 7328}
    }""",
        height=150,
    )


# Set the title
st.title("MultiQC Streamlit App")

# --- Data Loading --- #
data_loaded_successfully = False
bytes_data = None

# Check if data exists in session state
if st.session_state.bytes_data is not None:

    st.success(f"Data loaded from {st.session_state.data_source}")

    # Create a text element and let the reader know the data is loading.
    data_load_state = st.text("Extracting data...")
    try:
        # Use data from session state
        with ZipFile(BytesIO(st.session_state.bytes_data)) as zipfile:
            zipfile.extractall(path="./data") # Extract to a known directory
        data_load_state.text("Extracting data...done!")
        data_loaded_successfully = True
    except Exception as e:
        st.error(f"Error extracting ZIP file: {e}")
        st.stop()

    # Parse logs
    data_parse_state = st.text("Parsing logs...")
    try:
        multiqc.parse_logs("./data")
        data_parse_state.text("Parsing logs...done!")
    except Exception as e:
        st.error(f"Error parsing logs: {e}")
        st.stop()

    with st.expander("Parsed data details"):
        st.subheader("Modules")
        st.write(multiqc.list_modules())
        st.subheader("Plots")
        st.write(multiqc.list_plots())
        st.subheader("Samples")
        st.write(multiqc.list_samples())

    # Show a table (assuming HiCUP exists in the uploaded data, original behavior)
    st.header("HiCUP module data")
    st.write("HiCUP QC data from the parsed logs.")
    try:
        hicup_data = multiqc.get_module_data(module="HiCUP")
        assert(hicup_data)
        st.dataframe(pd.DataFrame(hicup_data))
    except (KeyError, AssertionError):
        st.warning("HiCUP module not found in parsed data.")

    # Show a plot (assuming HiCUP plot exists, original behavior)
    st.header("HiCUP plot")
    st.write("This is MultiQC plot from the parsed data.")
    try:
        hicup_plot = multiqc.get_plot("HiCUP", "Read Pair Filtering")
        hicup_plot_pt = hicup_plot.get_figure(0)
        hicup_plot_pt.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=go.layout.XAxis(),
            yaxis=go.layout.YAxis(),
            modebar=go.layout.Modebar(),
        )
        st.plotly_chart(hicup_plot_pt)
    except (KeyError, IndexError, AttributeError):
        st.warning("Could not retrieve HiCUP plot 'Read Pair Filtering'.")

    # Add a plot with some custom data
    st.header("Custom plot")
    st.write("This is a custom plot with some custom data contained in this script.")
    try:
        custom_data = json.loads(EXAMPLE_CUSTOM_DATA)
        module = multiqc.BaseMultiqcModule(
            anchor="my_metrics",
        )
        custom_plot = bargraph.plot(
            data=custom_data,
            pconfig={"id": "my_metrics_barplot", "title": "My metrics"},
        )

        # Show a single plot
        custom_plot_pt = custom_plot.get_figure(0)
        custom_plot_pt.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=go.layout.XAxis(),
            yaxis=go.layout.YAxis(),
            modebar=go.layout.Modebar(),
        )
        st.plotly_chart(custom_plot_pt)

        # Add custom plot section to the report
        module.add_section(plot=custom_plot)
        multiqc.report.modules.append(module)

    except json.JSONDecodeError as e:
        st.error(f"Error parsing Custom Data JSON: {e}")
    except Exception as e:
        st.error(f"Error generating custom plot: {e}")

    # Generate the report
    st.header("MultiQC Report")
    report_gen_state = st.text("Generating MultiQC report...")
    try:
        multiqc.write_report(output_dir="multiqc_report", force=True)
        html_data = open("multiqc_report/multiqc_report.html").read()
        components.html(html_data, scrolling=True, height=500)
        report_gen_state.text("Generating MultiQC report...done!")
    except Exception as e:
         st.error(f"Error generating MultiQC report: {e}")
         report_gen_state.text(f"Error generating MultiQC report: {e}")

else:
    st.info("Please select an input method and provide data using the sidebar to start the analysis.")

