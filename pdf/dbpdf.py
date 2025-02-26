from PyPDF2 import PdfWriter, PdfReader
import os
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
import io




# Define directory paths
pdf_dir = os.path.join(os.getcwd(), "pdf")
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)

file_path = os.path.join(pdf_dir, "esempio.pdf")
output_path = os.path.join(pdf_dir, "output.pdf")


def create_gradient(drawing, width, height, y_pos):
    """Create gradient effect"""
    num_steps = 50
    for i in range(num_steps):
        segment_height = height / num_steps
        segment_y = y_pos + (i * segment_height)
        intensity = 0.5 - (i / (num_steps * 2))
        r = Drawing()
        r.add(Rect(
            0, segment_y, width, segment_height,
            fillColor=colors.Color(0.1, 0.2, 0.5 + intensity),
            strokeColor=None
        ))
        drawing.add(r)

def add_title(canvas, text, page_width, rect_y, rect_height):
    """Add centered title to PDF"""
    title_font_size = 36
    canvas.setFont("Helvetica", title_font_size)
    title_width = canvas.stringWidth(text, "Helvetica", title_font_size)
    title_x = (page_width - title_width) / 2
    title_y = rect_y + (rect_height/2) - 10
    canvas.setFillColor(colors.white)
    canvas.drawString(title_x, title_y, text)

def create_and_save_plot(df, title):
    """Create a plot and return it as an ImageReader object"""
    plt.figure(figsize=(6, 4))
    
    try:
        # Clean the dataframe by converting string columns to numeric where possible
        df_clean = df.copy()
        for col in df.columns:
            # Try to convert strings to numeric, replacing errors with NaN
            if df[col].dtype == 'object':
                try:
                    # Remove any commas and spaces from numbers
                    df_clean[col] = df[col].str.replace(',', '').str.replace(' ', '')
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                except:
                    continue

        # Get only numeric columns
        numeric_cols = df_clean.select_dtypes(include=['float64', 'int64']).columns
        numeric_df = df_clean[numeric_cols].dropna(axis=1, how='all')
        
        if len(numeric_df.columns) == 0:
            # If no numeric columns, create a simple text plot
            plt.text(0.5, 0.5, "No numeric data available for plotting",
                    horizontalalignment='center',
                    verticalalignment='center')
            plt.axis('off')
        elif len(numeric_df.columns) == 1:
            # Plot single column against index
            valid_data = numeric_df[numeric_df.columns[0]].dropna()
            plt.plot(range(len(valid_data)), valid_data)
            plt.xlabel('Index')
            plt.ylabel(numeric_df.columns[0])
        else:
            # Plot first two numeric columns
            x_col = numeric_df.columns[0]
            y_col = numeric_df.columns[1]
            valid_mask = numeric_df[[x_col, y_col]].notna().all(axis=1)
            plt.plot(numeric_df[x_col][valid_mask], numeric_df[y_col][valid_mask])
            plt.xlabel(x_col)
            plt.ylabel(y_col)

        # Add title and grid
        plt.title(title)
        plt.grid(True)
        
        # Save plot to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return ImageReader(buf)
        
    except Exception as e:
        print(f"Error creating plot: {str(e)}")
        plt.close()
        raise

def create_pdf_report(df, title, output_path):
    """Create a PDF report with data and plot"""
    try:
        c = canvas.Canvas(output_path, pagesize=letter)
        page_width, page_height = letter
        
        # Create header with gradient
        rect_height = page_height * 0.30
        rect_y = page_height - rect_height + 20
        d = Drawing(page_width, page_height)
        create_gradient(d, page_width, rect_height, rect_y)
        renderPDF.draw(d, c, 0, 0)
        
        # Add title and author
        add_title(c, title, page_width, rect_y, rect_height)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 14)
        c.drawString(30, rect_y - 70, "Luca Albanese")
        
        # Add data
        y_position = rect_y - 100
        
        # Add column headers
        c.setFont("Helvetica-Bold", 12)
        header_text = ", ".join(df.columns)
        c.drawString(50, y_position, f"Columns: {header_text}")
        y_position -= 20
        
        # Add data rows with better formatting
        c.setFont("Helvetica", 12)
        for i, row in df.head(25).iterrows():
            # Format each value appropriately
            formatted_values = []
            for val in row:
                if pd.isna(val):
                    formatted_values.append("N/A")
                elif isinstance(val, (int, float)):
                    formatted_values.append(f"{val:.2f}" if isinstance(val, float) else str(val))
                else:
                    formatted_values.append(str(val))
            
            row_text = ", ".join(formatted_values)
            c.drawString(50, y_position, row_text[:60] + "..." if len(row_text) > 60 else row_text)
            y_position -= 15
        
        # Add plot
        plot_img = create_and_save_plot(df, title)
        c.drawImage(plot_img, 300, y_position, width=250, height=200)
        
        c.save()
        print(f"Created PDF report: {output_path}")
        
    except Exception as e:
        print(f"Error creating PDF report: {str(e)}")
        raise

def create_coastal_erosion_report(main_df, additional_files, output_path):
    """Create a PDF report for coastal erosion with multiple datasets"""
    try:
        c = canvas.Canvas(output_path, pagesize=letter)
        page_width, page_height = letter

        # Create header with gradient for first page
        rect_height = page_height * 0.30
        rect_y = page_height - rect_height + 20
        d = Drawing(page_width, page_height)
        create_gradient(d, page_width, rect_height, rect_y)
        renderPDF.draw(d, c, 0, 0)
        
        # Add title and author
        add_title(c, "Coastal Erosion Analysis", page_width, rect_y, rect_height)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 14)
        c.drawString(30, rect_y - 70, "Luca Albanese ")
        
        y_position = rect_y - 100

        # Add all plots at the top
        plots = create_four_plots(main_df, additional_files)
        # First row of plots
        c.drawImage(plots[0], 50, y_position - 150, width=250, height=150)
        c.drawImage(plots[1], 300, y_position - 150, width=250, height=150)
        # Second row of plots
        c.drawImage(plots[2], 50, y_position - 300, width=250, height=150)
        c.drawImage(plots[3], 300, y_position - 300, width=250, height=150)

        y_position = y_position - 320  # Move position below plots

        # Add datasets
        y_position = add_dataset_to_pdf(c, main_df, "Main Coastal Erosion Data", y_position)
        
        # Add additional datasets
        for file_name, df in additional_files.items():
            if y_position < 100:  # Check if we need a new page
                c.showPage()
                y_position = 750
            y_position = add_dataset_to_pdf(c, df, file_name, y_position)
        
        c.save()
        print(f"Created enhanced coastal erosion report: {output_path}")
        
    except Exception as e:
        print(f"Error creating coastal erosion report: {str(e)}")
        raise

def plot_dataset(df, title):
    """Plot a single dataset with improved styling"""
    try:
        # Convert data to numeric, dropping non-numeric values
        numeric_df = df.apply(pd.to_numeric, errors='coerce')
        numeric_df = numeric_df.dropna(axis=1, how='all')
        
        if len(numeric_df.columns) >= 2:
            x_col = numeric_df.columns[0]
            y_col = numeric_df.columns[1]
            valid_data = numeric_df[[x_col, y_col]].dropna()
            
            # Enhanced plot styling
            plt.plot(valid_data[x_col], valid_data[y_col], 
                    linewidth=2, 
                    marker='o', 
                    markersize=4,
                    color='#1f77b4',
                    linestyle='-',
                    markerfacecolor='white')
            plt.xlabel(x_col, fontsize=10)
            plt.ylabel(y_col, fontsize=10)
        else:
            # Single column plot with enhanced styling
            valid_data = numeric_df[numeric_df.columns[0]].dropna()
            plt.plot(range(len(valid_data)), valid_data,
                    linewidth=2, 
                    marker='o', 
                    markersize=4,
                    color='#1f77b4',
                    linestyle='-',
                    markerfacecolor='white')
            plt.xlabel('Index', fontsize=10)
            plt.ylabel(numeric_df.columns[0], fontsize=10)
        
        plt.title(title, fontsize=12, pad=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().tick_params(labelsize=8)
        plt.tight_layout(pad=2.0)
        return True
        
    except Exception as e:
        print(f"Error in plot_dataset: {str(e)}")
        plt.text(0.5, 0.5, "Error plotting data", 
                horizontalalignment='center', 
                verticalalignment='center')
        plt.axis('off')
        return False

def save_plot_to_buffer():
    """Save the current plot to a buffer and return it"""
    buf = io.BytesIO()
    try:
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        plt.close()
        # Verify the buffer contains valid image data
        from PIL import Image
        Image.open(buf).verify()
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Error saving plot to buffer: {str(e)}")
        plt.close()
        buf.close()
        return None

def create_four_plots(main_df, additional_files):
    """Create four separate plots and return them as ImageReaders"""
    plots = []
    
    # Use a built-in style that's always available
    plt.style.use('classic')
    
    # Create main dataset plot
    plt.figure(figsize=(6, 4))
    if plot_dataset(main_df, "Main Coastal Erosion"):
        buf = save_plot_to_buffer()
        if buf:
            plots.append(ImageReader(buf))
    
    # Create plots for additional datasets
    for name, df in additional_files.items():
        plt.figure(figsize=(6, 4))
        if plot_dataset(df, name):
            buf = save_plot_to_buffer()
            if buf:
                plots.append(ImageReader(buf))
    
    # Ensure we have exactly 4 plots by adding empty plots if necessary
    while len(plots) < 4:
        plt.figure(figsize=(6, 4))
        plt.text(0.5, 0.5, "No data available", 
                horizontalalignment='center', 
                verticalalignment='center')
        plt.axis('off')
        buf = save_plot_to_buffer()
        if buf:
            plots.append(ImageReader(buf))
    
    return plots[:4]  # Return exactly 4 plots

def add_dataset_to_pdf(c, df, title, y_position):
    """Add a dataset section to the PDF"""
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, f"Dataset: {title}")
    y_position -= 20
    
    c.setFont("Helvetica-Bold", 12)
    header_text = ", ".join(df.columns)
    c.drawString(50, y_position, f"Columns: {header_text}")
    y_position -= 20
    
    c.setFont("Helvetica", 12)
    for i, row in df.head(10).iterrows():  # Show only first 10 rows of each dataset
        formatted_values = []
        for val in row:
            if pd.isna(val):
                formatted_values.append("N/A")
            elif isinstance(val, (int, float)):
                formatted_values.append(f"{val:.2f}" if isinstance(val, float) else str(val))
            else:
                formatted_values.append(str(val))
        
        row_text = ", ".join(formatted_values)
        c.drawString(50, y_position, row_text[:60] + "..." if len(row_text) > 60 else row_text)
        y_position -= 15
    
    y_position -= 20  # Add space between datasets
    return y_position

def create_combined_plot(main_df, additional_files):
    """Create a combined plot with data from all files"""
    plt.figure(figsize=(12, 6))
    
    # Plot main dataset
    plt.subplot(2, 2, 1)
    create_and_save_plot(main_df, "Main Coastal Erosion")
    
    # Plot additional datasets
    for i, (name, df) in enumerate(additional_files.items(), start=2):
        plt.subplot(2, 2, i)
        create_and_save_plot(df, name)
    
    plt.tight_layout()
    
    # Save combined plot
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return ImageReader(buf)

def process_all_datasets():
    """Process all datasets and create separate PDFs"""
    try:
        # Coastal erosion processing (existing code)
        coastal_erosion_files = {
            'dry_beach': pd.read_csv('data/hazard/dry_beach.csv'),
            'flood': pd.read_csv('data/hazard/flood.csv'),
            'hazard_weights': pd.read_csv('data/hazard/hazard_weights.csv')
        }
        
        main_df = pd.read_csv('data/hazard/coastal_erosion.csv')
        output_path = os.path.join(pdf_dir, 'coastal_erosion_report.pdf')
        create_coastal_erosion_report(main_df, coastal_erosion_files, output_path)
        
        # Economic data processing with multiple files
        economic_files = {
            'Main Economic': pd.read_csv('data/risk/economia.csv'),
            'EI Depth': pd.read_csv('data/risk/ei_depth.csv'),
            'EI Percentage': pd.read_csv('data/risk/ei_percentage.csv'),
            'Environment': pd.read_csv('data/risk/medio_ambiente.csv'),
            'Population': pd.read_csv('data/risk/poblacion.csv')
        }
        
        output_path = os.path.join(pdf_dir, 'economic_report.pdf')
        create_economic_report(economic_files, output_path)
        
        # Process Hz-BCT curves
        df_curves = pd.read_csv('data/curves/hz-bct.csv')
        output_path = os.path.join(pdf_dir, 'hz_bct_report.pdf')
        create_pdf_report(df_curves, 'Hz-BCT Curves', output_path)
        
        print("All PDFs have been created successfully!")
        
    except Exception as e:
        print(f"Error in process_all_datasets: {str(e)}")
        raise

def create_economic_report(data_files, output_path):
    """Create a PDF report for economic data with multiple datasets"""
    try:
        c = canvas.Canvas(output_path, pagesize=letter)
        page_width, page_height = letter

        # Create header with gradient
        rect_height = page_height * 0.30
        rect_y = page_height - rect_height + 20
        d = Drawing(page_width, page_height)
        create_gradient(d, page_width, rect_height, rect_y)
        renderPDF.draw(d, c, 0, 0)
        
        # Add title and author
        add_title(c, "Economic Impact Analysis", page_width, rect_y, rect_height)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 14)
        c.drawString(30, rect_y - 70, "Luca Albanese ")
        
        y_position = rect_y - 100

        # Add all plots at the top
        plots = create_four_plots(data_files['Main Economic'], 
                                {k: v for k, v in data_files.items() if k != 'Main Economic'})
        
        # First row of plots
        c.drawImage(plots[0], 50, y_position - 150, width=250, height=150)
        c.drawImage(plots[1], 300, y_position - 150, width=250, height=150)
        # Second row of plots
        c.drawImage(plots[2], 50, y_position - 300, width=250, height=150)
        c.drawImage(plots[3], 300, y_position - 300, width=250, height=150)

        y_position = y_position - 320  # Move position below plots

        # Add all datasets
        for name, df in data_files.items():
            if y_position < 100:  # Check if we need a new page
                c.showPage()
                y_position = 750
            y_position = add_dataset_to_pdf(c, df, name, y_position)
        
        c.save()
        print(f"Created enhanced economic report: {output_path}")
        
    except Exception as e:
        print(f"Error creating economic report: {str(e)}")
        raise

if __name__ == "__main__":
    process_all_datasets()


