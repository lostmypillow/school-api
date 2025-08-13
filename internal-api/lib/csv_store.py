from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import DEPS_CSV_PATH, USERS_CSV_PATH
from lib.decrypt_pwd import decrypt_pwd
from lib.die import _die


@dataclass
class UserData:
    uid: str
    cn: str
    givenname: str
    sn: str
    pwd: str | None
    main_grp: str
    other_grp: list | None
    mail: str


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

        return df.map(
            lambda x: (
                None
                if (
                    x is None
                    or (isinstance(x, float) and pd.isna(x))
                    or (isinstance(x, str) and x.strip().lower() in null_sentinels)
                )
                else (x.strip() if isinstance(x, str) else x)
            )
        )

    def _load_users_df(self) -> pd.DataFrame:
        df = pd.read_csv(self.users_csv)
        return self._clean_df(df)

    def _load_deps_df(self) -> pd.DataFrame:
        if self._deps_df is None:
            self._deps_df = self._clean_df(pd.read_csv(self.deps_csv))
        return self._deps_df

    def _split_chinese_name(self, full_name: str) -> tuple:
        """Split a Chinese name into a last name (surname) and first name based on length.

        Args
        -------
            full_name (str): The full Chinese name (e.g., "张伟", "欧阳修").

        Returns
        -------
            tuple: A tuple containing (last_name, first_name).
        """
        name_length = len(full_name)

        # For names with 2 characters 
        if name_length == 2:
            last_name = full_name[0]
            first_name = full_name[1]

        # For names with 3 characters 
        elif name_length == 3:
            # We assume single-character surnames are more common than double-character ones
            last_name = full_name[0]
            first_name = full_name[1:]

        # For names with 4 or more characters
        elif name_length >= 4:
            # Double surnames are more likely here
            last_name = full_name[:2]
            first_name = full_name[2:]

        # For names with 1 character, it's ambiguous
        else:
            last_name = full_name
            first_name = ""

        return (last_name, first_name)

    def load_row(self, row_index: int) -> UserData:
        df = self._load_users_df()
        if row_index < 0 or row_index >= len(df):
            _die(f"Row index {row_index} out of range (0..{len(df) - 1}).")
        row = df.iloc[row_index]
        dep_df = pd.read_csv(DEPS_CSV_PATH)

        main_grp_id: int = 0
        dep_row = dep_df.loc[dep_df["自動編號"] == int(row["main_grp"]), "group"]
        main_grp_id = dep_row.iloc[0]
        other_grp_ids = []
        if row.get("other_grp") is not None and (row.get("other_grp") != row["main_grp"]):

            for dep_id in str(row["other_grp"]).split(","):

                other_grp_ids.append(dep_df.loc[dep_df["自動編號"] == int(dep_id), "group"].iloc[0]) 
        print(row["other_grp"])

        return UserData(
            uid=str(row["uid"]) if row.get("uid") is not None else "",
            cn=str(row["cn"]) if row.get("cn") is not None else "",
            givenname=self._split_chinese_name(row["cn"])[1],
            sn=self._split_chinese_name(row["cn"])[0],
            pwd=decrypt_pwd(row["pwd"]) if row.get("pwd") is not None else str(row["uid"]),
            main_grp=main_grp_id,
            other_grp=other_grp_ids, 
        )

    def load_all_users(self) -> list[UserData]:
        users_df = self._load_users_df()
        deps_df = self._load_deps_df()
        user_list = []

        for _, row in users_df.iterrows():
            main_grp_id = None
            dep_row = deps_df.loc[deps_df["自動編號"] == row["main_grp"], "group"]
            if not dep_row.empty:
                main_grp_id = dep_row.iloc[0]
            other_grp_ids = []
            if pd.notna(row.get("other_grp")) and (row.get("other_grp") != row["main_grp"]):
                dep_ids = str(row["other_grp"]).split(",")
                for dep_id in dep_ids:
                    dep_id = dep_id.strip()
                    if dep_id:
                        other_dep_row = deps_df.loc[deps_df["自動編號"] == int(dep_id), "group"]
                        if not other_dep_row.empty:
                            other_grp_ids.append(other_dep_row.iloc[0])

            user_list.append(
                UserData(
                    uid="" + str(row["uid"]) if pd.notna(row.get("uid")) else "",
                    cn=str(row["cn"]) if pd.notna(row.get("cn")) else "",
                    givenname=self._split_chinese_name(row["cn"])[1] if pd.notna(row.get("cn")) else "",
                    sn=self._split_chinese_name(row["cn"])[0] if pd.notna(row.get("cn")) else "",
                    pwd=decrypt_pwd(row["pwd"]) if pd.notna(row.get("pwd")) else str(row["uid"]),
                    main_grp=main_grp_id,
                    other_grp=other_grp_ids,
                    mail=str(row["uid"]) + "@km.",
                )
            )

        return user_list

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
