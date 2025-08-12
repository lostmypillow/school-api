from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import DEPS_CSV_PATH, USERS_CSV_PATH
from lib.die import _die


@dataclass
class UserData:
    uid: str
    cn: str
    pwd: str | None
    main_grp: int
    other_grp: list | None

class CSVStore:
    """
    OOP wrapper around your CSVs.

      - users CSV (uid, cn, pwd, main_grp, other_grp)
      - deps CSV (自動編號 -> group)
    """

    def __init__(self, users_csv: Path = USERS_CSV_PATH, deps_csv: Path = DEPS_CSV_PATH) -> None:
        self.users_csv = Path(users_csv)
        self.deps_csv = Path(deps_csv)
        self._deps_df: pd.DataFrame | None = None

    @staticmethod
    def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
        null_sentinels = {"null", "nan", "none", ""}

        return df.applymap(
        lambda x: (
            None
            if (
                x is None
                or (isinstance(x, float) and pd.isna(x))
                or (isinstance(x, str) and x.strip().lower() in null_sentinels)
            )
            else (x.strip() if isinstance(x, str) else x)
        ))

    def _load_users_df(self) -> pd.DataFrame:
        df = pd.read_csv(self.users_csv)
        return self._clean_df(df)

    def _load_deps_df(self) -> pd.DataFrame:
        if self._deps_df is None:
            self._deps_df = self._clean_df(pd.read_csv(self.deps_csv))
        return self._deps_df

    def load_row(self, row_index: int) -> UserData:
        df = self._load_users_df()
        if row_index < 0 or row_index >= len(df):
            _die(f"Row index {row_index} out of range (0..{len(df)-1}).")
        row = df.iloc[row_index]
        return UserData(
            uid=str(row["uid"]) if row.get("uid") is not None else "",
            cn=str(row["cn"]) if row.get("cn") is not None else "",
            pwd=str(row["pwd"]) if row.get("pwd") is not None else None,
            main_grp=str(row["main_grp"]) if row.get("main_grp") is not None else None,
            other_grp=str(row["other_grp"]) if row.get("other_grp") is not None else None,
        )

    def load_all(self) -> list[UserData]:
        df = self._load_users_df()
        records: list[UserData] = []
        for _, r in df.iterrows():
            records.append(
                UserData(
                    uid=str(r["uid"]) if r.get("uid") is not None else "",
                    cn=str(r["cn"]) if r.get("cn") is not None else "",
                    pwd=str(r["pwd"]) if r.get("pwd") is not None else None,
                    main_grp=str(r["main_grp"]) if r.get("main_grp") is not None else None,
                    other_grp=str(r["other_grp"]) if r.get("other_grp") is not None else None,
                ),
            )
        return records

    def resolve_main_group(self, main_grp_value: str | None) -> str | None:
        """
        Map your 'main_grp' (自動編號) to a real group name using deps.csv.

        Returns the resolved group (string) or None if not found / not provided.
        """
        if not main_grp_value:
            return None
        dep_df = self._load_deps_df()
        try:
            auto_no = int(main_grp_value)
        except (TypeError, ValueError):
            # if it's already a name, just return it
            return str(main_grp_value)

        dep_row = dep_df.loc[dep_df["自動編號"] == auto_no, "group"]
        if not dep_row.empty:
            return str(dep_row.iloc[0])
        return None
