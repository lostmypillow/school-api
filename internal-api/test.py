from lib.decrypt_pwd import decrypt_pwd

from rich import print


# def decrypt_pwd(encrypted: str) -> str:
#     """
#     Reverse of: "".join(f"{ord(c)}0{i + 1}" for i, c in enumerate(plain_password))
#     """
#     chars = []
#     i = 0
#     while i < len(encrypted):
#         zero_pos = encrypted.index('0', i)
#         codepoint = int(encrypted[i:zero_pos])
#         chars.append(chr(codepoint))

#         # Skip past '0' and the position number (which can be multi-digit)
#         j = zero_pos + 1
#         while j < len(encrypted) and encrypted[j].isdigit():
#             j += 1
#         i = j

#     return "".join(chars)

print(decrypt_pwd("97011220212003570456055606"))