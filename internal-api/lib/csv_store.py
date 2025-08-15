from pathlib import Path

import pandas as pd
import typer

from config import DEPS_CSV_PATH, USERS_CSV_PATH
from lib.decrypt_pwd import decrypt_pwd
from lib.user_dataclass import UserData


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
            ),
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
        if name_length == 2:  # noqa: PLR2004
            last_name = full_name[0]
            first_name = full_name[1]

        # For names with 3 characters
        elif name_length == 3:  # noqa: PLR2004
            # We assume single-character surnames are more common than double-character ones
            last_name = full_name[0]
            first_name = full_name[1:]

        # For names with 4 or more characters
        elif name_length >= 4:  # noqa: PLR2004
            # Double surnames are more likely here
            last_name = full_name[:2]
            first_name = full_name[2:]

        # For names with 1 character, it's ambiguous
        else:
            last_name = full_name
            first_name = ""

        return (last_name, first_name)


    def load_all_users(self) -> list[UserData]:
        users_df = self._load_users_df()
        deps_df = self._load_deps_df()
        user_list = []

        for _, row in users_df.iterrows():
            main_grp_name = ""
            dep_row = deps_df.loc[deps_df["自動編號"] == row["main_grp"], "group"]
            if not dep_row.empty:
                main_grp_name = dep_row.iloc[0] # type: ignore  # noqa: PGH003
            other_grp_names = []
            if pd.notna(row.get("other_grp")) and (row.get("other_grp") != row["main_grp"]):
                dep_ids = str(row["other_grp"]).split(",")
                for dep_id in dep_ids:
                    dep_id = dep_id.strip()  # noqa: PLW2901
                    if dep_id:
                        other_dep_row = deps_df.loc[deps_df["自動編號"] == int(dep_id), "group"]
                        if not other_dep_row.empty:
                            other_grp_names.append(other_dep_row.iloc[0])

            user_list.append(
                UserData(
                    uid="E" + str(row["uid"]) if pd.notna(row.get("uid")) else "",
                    employeenumber=str(row["uid"]) if pd.notna(row.get("uid")) else "",
                    cn=str(row["cn"]) if pd.notna(row.get("cn")) else "",
                    givenname=self._split_chinese_name(row["cn"])[1]
                    if pd.notna(row.get("cn"))
                    else "",
                    sn=self._split_chinese_name(row["cn"])[0] if pd.notna(row.get("cn")) else "",
                    pwd=decrypt_pwd(row["pwd"]) if pd.notna(row.get("pwd")) else str(row["uid"]),
                    main_grp=main_grp_name,
                    main_grp_id=row["main_grp"] if row["main_grp"] else "0",
                    other_grp=other_grp_names,
                    other_grp_ids=str(row["other_grp"]).split(",") if str(row["other_grp"]) else [],
                    mail=str(row["uid"]) + "@km.",
                    departmentnumber=row["main_grp"] if row["main_grp"] else "0"
                ),
            )

        return user_list
    def load_all_deps(self) -> list[dict]:
        """Load the deps CSV into a list of dictionaries.

        Returns
        -------
            list[dict]: A list of dictionaries, where each dictionary
                        represents a row from the deps CSV.
        """
        deps_df = self._load_deps_df()
        return deps_df.to_dict("records")

