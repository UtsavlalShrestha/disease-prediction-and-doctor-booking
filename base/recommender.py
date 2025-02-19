import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict, Any


class DoctorRecommender:
    def __init__(self, doctors: List[Dict[str, Any]], specialty: str, disease_description: str):
        """
        Initialize the recommender with doctor data, user specialty, and disease description.
        """
        self.doctors = doctors
        self.specialty = specialty.strip()
        self.disease_description = disease_description.strip()

    def _prepare_dataframe(self) -> pd.DataFrame:
        """
        Convert doctor data into a pandas DataFrame and create combined text features.
        """
        df = pd.DataFrame(self.doctors)
        df.rename(columns={'speciality__name': 'specialty'}, inplace=True)
        df['description'] = df['description'].fillna('')
        df['combined_features'] = df['specialty'] + " " + df['description']
        return df

    def _compute_text_similarity(self, df: pd.DataFrame) -> List[float]:
        """
        Compute text similarity manually using cosine similarity.
        """
        if not self.disease_description:
            return [0] * len(df)

        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df['combined_features']).toarray()
        disease_vector = tfidf.transform([self.disease_description]).toarray()[0]

        similarities = []
        for vector in tfidf_matrix:
            dot_product = np.dot(disease_vector, vector)
            norm_a = np.linalg.norm(disease_vector)
            norm_b = np.linalg.norm(vector)
            similarity = dot_product / (norm_a * norm_b) if norm_a * norm_b != 0 else 0
            similarities.append(similarity)

        return similarities

    def _compute_experience_similarity(self, df: pd.DataFrame) -> List[float]:
        """
        Normalize and compute experience similarity.
        """
        if df['experience'].isnull().all():
            return [0] * len(df)

        max_experience = df['experience'].max()
        return df['experience'] / max_experience if max_experience > 0 else [0] * len(df)

    def _compute_specialty_similarity(self, df: pd.DataFrame) -> List[float]:
        """
        Compute specialty similarity (1 if matches, 0 otherwise).
        """
        return (df['specialty'] == self.specialty).astype(float)

    def recommend(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Generate the top K doctor recommendations.
        """
        if not self.doctors:
            return []

        df = self._prepare_dataframe()

        df['text_similarity'] = self._compute_text_similarity(df)
        df['experience_similarity'] = self._compute_experience_similarity(df)
        df['specialty_similarity'] = self._compute_specialty_similarity(df)

        df['similarity_score'] = (
            (0.5 * df['specialty_similarity']) +
            (0.25 * df['experience_similarity']) +
            (0.25 * df['text_similarity'])
        )
        df_sorted = df.sort_values(by='similarity_score', ascending=False)
        return df_sorted.head(top_k).to_dict('records')
