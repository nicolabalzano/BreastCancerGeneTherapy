# Breast Cancer Gene Therapy Analysis Tool

## Overview

This repository contains a comprehensive tool for breast cancer gene analysis and therapy recommendation. The system uses machine learning algorithms, specifically CatBoost, to predict the most important genes associated with breast cancer tumors and provides therapeutic insights based on the latest scientific research.

## Features

- **Gene Expression Analysis**: Process RNA sequencing data and miRNA quantification files
- **Machine Learning Prediction**: Utilizes CatBoost algorithm to identify the most significant genes in breast cancer
- **Therapy Recommendation**: Provides therapy suggestions based on current scientific research for the most important predicted genes
- **Web Interface**: User-friendly frontend for uploading data and viewing results
- **API Backend**: RESTful API for programmatic access to the analysis tools

## Project Structure

```
├── backendPrediction/          # Backend API service
│   ├── flask_app.py           # Main Flask application
│   ├── prediction.py          # CatBoost prediction logic
│   ├── preprocessing.py       # Data preprocessing utilities
│   └── assets/               # Model files and sample data
├── frontend/                  # Web interface
│   ├── app.py                # Frontend Flask application
│   └── templates/            # HTML templates
├── LLM/                      # Language model integration
└── docker-compose files     # Container orchestration
```

## Requirements

- Docker
- Docker Compose

## Running the Application

### Development Mode

To run the application in development mode with hot reloading and debugging features:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Production Mode

To run the application in production mode:

```bash
docker-compose up --build
```

## How It Works

1. **Data Upload**: Users can upload RNA sequencing data files (`.tsv`) and miRNA quantification files (`.txt`)
2. **Preprocessing**: The system processes and normalizes the genetic data
3. **Prediction**: CatBoost algorithm analyzes the data to identify the most important genes associated with breast cancer
4. **Research Integration**: The system queries current scientific literature to provide therapy recommendations based on the identified genes
5. **Results Visualization**: Users receive detailed reports with gene importance rankings and therapeutic suggestions

## Input Data Format

The system accepts the following file formats:
- **RNA-seq data**: `.tsv` files with augmented STAR gene counts
- **miRNA data**: `.txt` files with miRBase21 quantification data
- **Isoform data**: `.txt` files with miRBase21 isoform quantification

## API Endpoints

The backend provides RESTful API endpoints for:
- File upload and processing
- Gene prediction analysis
- Therapy recommendation retrieval
- Results download

## Scientific Background

This tool leverages:
- **CatBoost**: A gradient boosting algorithm particularly effective for genomic data
- **Gene Expression Analysis**: Processing of RNA sequencing and miRNA data
- **Scientific Literature Integration**: Real-time access to current research for therapy recommendations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is developed for research and educational purposes in the field of cancer genomics and personalized medicine.

## Support

For questions or issues, please refer to the documentation or create an issue in the repository.
