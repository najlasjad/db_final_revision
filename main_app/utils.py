import joblib
import pandas as pd
import os
from django.conf import settings
from mlxtend.frequent_patterns import apriori, association_rules

def load_model():
    model_path = os.path.join(settings.BASE_DIR, 'xgb_model_student_attendance.pkl')
    return joblib.load(model_path)

def predict_attendance(data):
    model = load_model()
    new_data = pd.DataFrame({
        'average_score': [data['average_score']],
        'grade': [data['grade']],
        'semester_id': [data['semester_id']],
        'course_id': [data['course_id']]
    })
    return model.predict(new_data)[0]

def course_recommendation(assessment_csv='course_recommendation.csv', output_csv='course_apriori_rules.csv'):
    if not os.path.exists(assessment_csv):
        raise FileNotFoundError(f"Assessment data file '{assessment_csv}' not found")

    df = pd.read_csv(assessment_csv)

    basket = (df.groupby(['stu_id', 'course_name'])['assessment_id']
              .count().unstack().reset_index().fillna(0)
              .set_index('stu_id'))

    basket = basket.applymap(bool)

    frequent_itemsets = apriori(basket, min_support=0.05, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.3)

    rules.to_csv(output_csv, index=False)

    return rules 

def analyze_courses(department, course1, course2, assessment_data, rules_data):

    # Filter assessment data by department
    dept_data = assessment_data[assessment_data['dept_name'] == department]
    
    if dept_data.empty:
        return {'error': f'No data found for department: {department}'}
        
    # Validate courses exist in the department
    available_courses = dept_data['course_name'].unique()
    if course1 not in available_courses:
        return {'error': f'Course "{course1}" not found in {department}'}
    if course2 not in available_courses:
        return {'error': f'Course "{course2}" not found in {department}'}
        
    # Get difficulty level and average score for each course
    course1_data = get_course_stats(dept_data, course1)
    course2_data = get_course_stats(dept_data, course2)
    
    # Find association rule between the two courses (in either direction)
    rule_data = find_association_rule(rules_data, course1, course2)
    
    # Generate recommendation based on rule data and difficulty levels
    recommendation = generate_recommendation(rule_data, course1, course2, 
                                             course1_data['difficulty'], 
                                             course2_data['difficulty'])
    
    # Prepare results
    result = {
        'department': department,
        'course1': {
            'name': course1,
            'difficulty': course1_data['difficulty'],
            'avg_score': course1_data['avg_score']
        },
        'course2': {
            'name': course2,
            'difficulty': course2_data['difficulty'],
            'avg_score': course2_data['avg_score']
        },
        'recommendation': recommendation,
        'rule_data': rule_data
    }
    
    return result

def get_course_stats(data, course_name):
    course_data = data[data['course_name'] == course_name]
    
    difficulty = course_data['difficulty_level'].unique().tolist()
    avg_score = round(course_data['score'].mean(), 2)
    
    return {
        'difficulty': difficulty,
        'avg_score': avg_score
    }

def find_association_rule(rules_df, course1, course2):
    rule1 = rules_df[
        (rules_df['antecedents'].str.contains(f"'{course1}'")) & 
        (rules_df['consequents'].str.contains(f"'{course2}'"))
    ]
    
    rule2 = rules_df[
        (rules_df['antecedents'].str.contains(f"'{course2}'")) & 
        (rules_df['consequents'].str.contains(f"'{course1}'"))
    ]
    
    
    if not rule1.empty and not rule2.empty:
        return rule1 if rule1['confidence'].values[0] > rule2['confidence'].values[0] else rule2
    elif not rule1.empty:
        return rule1
    elif not rule2.empty:
        return rule2
    else:
        return None

def generate_recommendation(rule_data, course1, course2, course1_difficulty, course2_difficulty):
 
    if 'hard' in [d.lower() for d in course1_difficulty] and 'hard' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Not Recommended to be taken together in the same semester as both have a high level of difficulty."
    if 'hard' in [d.lower() for d in course1_difficulty] and 'medium' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Request further consideration to be taken together in the same semester."
    if 'medium' in [d.lower() for d in course1_difficulty] and 'hard' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Request further consideration to be taken together in the same semester."
    if 'hard' in [d.lower() for d in course1_difficulty] and 'easy' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Acceptable to be taken in the same semester." 
    if 'easy' in [d.lower() for d in course1_difficulty] and 'hard' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Acceptable to be taken together in the same semester." 
    if 'medium' in [d.lower() for d in course1_difficulty] and 'medium' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Moderately recommended to be taken together in the same semester."
    if 'medium' in [d.lower() for d in course1_difficulty] and 'easy' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Recommended to be taken together in the same semester."
    if 'easy' in [d.lower() for d in course1_difficulty] and 'medium' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Recommended to be taken together in the same semester."
    if 'easy' in [d.lower() for d in course1_difficulty] and 'easy' in [d.lower() for d in course2_difficulty]:
        return f"{course1} dan {course2} Highly recommended to be taken together in the same semester."
    
    if rule_data is None or rule_data.empty:
        return f"{course1} dan {course2} Does not have a significant relationship based on historical data."
        
    confidence = rule_data['confidence'].values[0]
    lift = rule_data['lift'].values[0]
    
    if lift > 1:
        if confidence > 0.5:
            return f"{course1} dan {course2} Recommended to be taken together in the same semester."
        else:
            return f"{course1} dan {course2} Can be taken together in the same semester, but not significantly"
    else:
        return f"{course1} dan {course2} Not Recommended to be taken together in the same semester."


if __name__ == "__main__":
    course_recommendation()