import streamlit as st
import multiqc
from multiqc.plots import bargraph
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
import pandas as pd
import plotly.graph_objects as go
import json

# Sidebar
with st.sidebar:
    st.title("MultiQC Streamlit App")
    st.write("Edit below to see the output update in real-time.")

    # Set DATA_URL in an input
    DATA_URL = st.text_input("Demo Data URL", "https://multiqc.info/examples/hi-c/data.zip")

    # Set EXAMPLE_CUSTOM_DATA in an input
    EXAMPLE_CUSTOM_DATA = st.text_area("Custom Data", """{
        "sample 1": {"aligned": 23542, "not_aligned": 343},
        "sample 2": {"aligned": 1275, "not_aligned": 7328}
    }""")



# Set the title
st.title('MultiQC Streamlit App')

# Get some data
def download_and_unzip(url, extract_to='.'):
    http_response = urlopen(url)
    zipfile = ZipFile(BytesIO(http_response.read()))
    zipfile.extractall(path=extract_to)


# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading example logs...')
# Load 10,000 rows of data into the dataframe.
data = download_and_unzip(DATA_URL)
# Notify the reader that the data was successfully loaded.
data_load_state.text('Loading example logs...done!')


# Parse logs
data_parse_state = st.text('Parsing logs...')
multiqc.parse_logs('./data')
data_parse_state.text('Parsing logs...done!')

with st.expander("Parsed data details"):
    st.subheader("Modules")
    st.write(multiqc.list_modules())
    st.subheader("Plots")
    st.write(multiqc.list_plots())
    st.subheader("Samples")
    st.write(multiqc.list_samples())

# Show a table
st.header("HiCUP module data")
st.write("HiCUP QC data from the parsed logs.")
pd.DataFrame(multiqc.get_module_data(module="HiCUP"))

# Show a plot
st.header("HiCUP plot")
st.write("This is MultiQC plot from the parsed data.")
hicup_plot = multiqc.get_plot("HiCUP", "Read Pair Filtering")
hicup_plot_pt = hicup_plot.get_figure(0)
hicup_plot_pt.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=go.layout.XAxis(),
    yaxis=go.layout.YAxis(),
    modebar=go.layout.Modebar(),
)
st.plotly_chart(hicup_plot_pt)


# Add a plot with some custom data
st.header("Custom plot")
st.write("This is a custom plot with some custom data contained in this script.")
module = multiqc.BaseMultiqcModule(
    anchor="my_metrics",
)
custom_plot = bargraph.plot(
    data=json.loads(EXAMPLE_CUSTOM_DATA),
    pconfig={
        "id": "my_metrics_barplot",
        "title": "My metrics"
    }
)

# Show a single plot
custom_plot_pt = custom_plot.get_figure(0)
custom_plot_pt.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=go.layout.XAxis(),
    yaxis=go.layout.YAxis(),
    modebar=go.layout.Modebar(),
)
st.plotly_chart(custom_plot_pt)



# Generate the report
module.add_section(
    plot=custom_plot
)
multiqc.report.modules.append(module)
# multiqc.write_report()
