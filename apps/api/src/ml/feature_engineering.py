"""
Feature Engineering Pipeline - Istanbul Konut Fiyat Tahmini

Categorical encoding, turev feature uretimi ve eksik deger yonetimi.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    from sklearn.preprocessing import LabelEncoder


class FeatureEngineer:
    """Egitim ve inference icin feature donusturme pipeline'i."""

    def __init__(self) -> None:
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.feature_columns: list[str] = []

    # ------------------------------------------------------------------
    # Egitim
    # ------------------------------------------------------------------
    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Egitim verisini donustur, feature ve target ayir.

        Returns:
            (X, y) - feature DataFrame ve target Series
        """
        import numpy as np
        from sklearn.preprocessing import LabelEncoder

        df = df.copy()

        # --- Turev feature'lar ---
        df["sqm_ratio"] = df["net_sqm"] / df["gross_sqm"].replace(0, np.nan)
        df["floor_ratio"] = df["floor"] / df["total_floors"].replace(0, np.nan)
        df["total_rooms"] = df["room_count"] + df["living_room_count"]
        df["rooms_per_sqm"] = df["total_rooms"] / df["net_sqm"].replace(0, np.nan)

        # --- Eksik deger kontrolu ---
        df = df.fillna(0)

        # --- Categorical encoding (Label Encoding) ---
        categorical_cols = ["district", "neighborhood", "property_type", "heating_type"]
        for col in categorical_cols:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            self.label_encoders[col] = le

        # --- Target ayir ---
        y = df["price"]

        # price_per_sqm olusturma — target leakage!
        drop_cols = ["price"]
        X = df.drop(columns=drop_cols)

        self.feature_columns = X.columns.tolist()
        return X, y

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Egitimde ogrenilenlerle yeni veri donustur."""
        import numpy as np

        df = df.copy()

        # --- Turev feature'lar ---
        df["sqm_ratio"] = df["net_sqm"] / df["gross_sqm"].replace(0, np.nan)
        df["floor_ratio"] = df["floor"] / df["total_floors"].replace(0, np.nan)
        df["total_rooms"] = df["room_count"] + df["living_room_count"]
        df["rooms_per_sqm"] = df["total_rooms"] / df["net_sqm"].replace(0, np.nan)

        df = df.fillna(0)

        # --- Categorical encoding ---
        categorical_cols = ["district", "neighborhood", "property_type", "heating_type"]
        for col in categorical_cols:
            le = self.label_encoders[col]
            # Bilinmeyen kategoriler icin guvenli donusum
            known = set(le.classes_)
            df[col] = df[col].astype(str).apply(
                lambda x, _k=known, _le=le: (
                    _le.transform([x])[0] if x in _k else -1
                )
            )

        # Sadece egitimde kullanilan sutunlari al (ayni sirada)
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0

        return df[self.feature_columns]

    # ------------------------------------------------------------------
    # Yardimcilar
    # ------------------------------------------------------------------
    def get_feature_names(self) -> list[str]:
        return self.feature_columns

    def save(self, path: str) -> None:
        """Pipeline'i joblib ile kaydet."""
        import joblib

        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "label_encoders": self.label_encoders,
                "feature_columns": self.feature_columns,
            },
            p / "feature_engineer.joblib",
        )

    def load(self, path: str) -> None:
        """Pipeline'i joblib ile yukle."""
        import joblib

        data = joblib.load(Path(path) / "feature_engineer.joblib")
        self.label_encoders = data["label_encoders"]
        self.feature_columns = data["feature_columns"]
