import pandas as pd
import streamlit as st
import os


def _get_file_extension(uploaded_file):
    """Extracts the lowercase file extension from an uploaded file or file path string."""
    if isinstance(uploaded_file, str):
        return os.path.splitext(uploaded_file)[1].lower()
    # Streamlit UploadedFile objects have a .name attribute
    if hasattr(uploaded_file, "name"):
        return os.path.splitext(uploaded_file.name)[1].lower()
    return ""


def _load_csv(uploaded_file):
    """Loads a CSV file, trying multiple encodings to handle non-UTF-8 data."""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=encoding)
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            st.error(f"Error reading CSV with {encoding} encoding: {str(e)}")
            return None

    st.error("Could not decode the CSV file. Please ensure it's a valid CSV with standard encoding.")
    return None


def _load_excel(uploaded_file):
    """Loads an Excel (.xlsx / .xls) file using openpyxl engine."""
    try:
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        return df
    except ImportError:
        st.error(
            "The `openpyxl` package is required to read Excel files. "
            "Install it with: `pip install openpyxl`"
        )
        return None
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return None


def _load_json(uploaded_file):
    """Loads a JSON file, attempting common orientations."""
    try:
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        df = pd.read_json(uploaded_file)
        return df
    except ValueError:
        # Retry with lines=True for newline-delimited JSON (JSON Lines)
        try:
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
            df = pd.read_json(uploaded_file, lines=True)
            return df
        except Exception as e:
            st.error(f"Error reading JSON file: {str(e)}")
            return None
    except Exception as e:
        st.error(f"Error reading JSON file: {str(e)}")
        return None


# File-type → loader mapping
_LOADERS = {
    ".csv": _load_csv,
    ".xlsx": _load_excel,
    ".xls": _load_excel,
    ".json": _load_json,
}

SUPPORTED_EXTENSIONS = list(_LOADERS.keys())


@st.cache_data(show_spinner="Loading data...")
def load_data(uploaded_file):
    """Loads a data file into a pandas DataFrame.

    Supports CSV, Excel (.xlsx/.xls), and JSON formats.
    The file type is detected automatically from the file extension.
    """
    ext = _get_file_extension(uploaded_file)

    loader = _LOADERS.get(ext)
    if loader is None:
        supported = ", ".join(SUPPORTED_EXTENSIONS)
        st.error(f"Unsupported file type '{ext}'. Supported formats: {supported}")
        return None

    return loader(uploaded_file)


def get_dataframe_info(df):
    """Returns basic information about the dataframe."""
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "duplicates": df.duplicated().sum(),
        "memory_usage": df.memory_usage(deep=True).sum() / 1024**2  # in MB
    }


def get_data_preview(df, rows=10):
    """Returns a limited preview of the dataset."""
    return df.head(rows)
