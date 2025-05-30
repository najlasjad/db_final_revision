# main_app/management/commands/eda_student_attendance.py

from django.core.management.base import BaseCommand
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import XGBRegressor
import joblib

from main_app.models import ModelNajla
from django.utils import timezone

class Command(BaseCommand):
    help = "Train XGBRegressor model on student attendance data and log model info"

    def handle(self, *args, **kwargs):
        try:
            # Load data
            df = pd.read_csv('all_data_joined.csv')
            self.stdout.write(self.style.SUCCESS('Data loaded successfully!'))

            # Preprocess data
            df['gender'] = df['gender'].map({'Male': 0, 'Female': 1})
            difficulty_map = {'Easy':1, 'Medium':2, 'Hard':3}
            df['difficulty_level'] = df['difficulty_level'].map(difficulty_map)

            # Define features and target
            y = df["attendance_percentage"]
            feature = ["average_score", "grade", "semester_id", "course_id"]
            X = df[feature]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Initialize model
            xgb_model = XGBRegressor(
                n_estimators=300,
                max_depth=3,
                learning_rate=0.01,
                subsample=0.8,
                colsample_bytree=0.7,
                random_state=42,
                colsample_bylevel=0.7,
                gamma=0.1,
                min_child_weight=5,
                reg_alpha=1,
                reg_lambda=2,
                subsample_bytree=1,
            )

            # Train model
            xgb_model.fit(X_train, y_train)

            # Evaluate model
            y_pred = xgb_model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            self.stdout.write(self.style.SUCCESS(f"Mean Squared Error: {mse}"))
            self.stdout.write(self.style.SUCCESS(f"R² Score: {r2}"))

            # Save model
            model_filename = '../../../xgb_model_student_attendance.pkl'
            joblib.dump(xgb_model, model_filename)
            self.stdout.write(self.style.SUCCESS(f"Model saved as {model_filename}"))

            # Save model info to database
            report = f"XGBRegressor Model: MSE={mse:.4f}, R²={r2:.4f}, trained on features: {', '.join(feature)}"
            modelnajla = ModelNajla.objects.create(
                model_name='XGBStudentAttendanceModel',
                model_file=model_filename,
                training_data='all_data_joined.csv',
                training_date=timezone.now(),
                model_summary=report
            )
            self.stdout.write(self.style.SUCCESS(f"Model info saved to DB: ID {modelnajla.id}"))

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"File not found: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error training model: {str(e)}"))
