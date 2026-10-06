# Databricks notebook source
# MAGIC %md
# MAGIC # Fourth Down — Free Edition batch validation
# MAGIC Runs the reference data through PySpark, writes two Delta tables, and checks every forecast against the local Python implementation.
# MAGIC The embedded CSV is an exact copy of player_games.csv uploaded to the private AWS S3 bucket fourth-down-adam-skarre-20261006.
# MAGIC **This run does not read S3 directly.** It demonstrates separate AWS storage and Databricks processing with an explicit file-copy boundary.
# MAGIC Only the two tables in the dedicated fourth_down_portfolio schema are replaced when rerun.
# MAGIC Data: 164 selected historical player-game records, 2024. Source attribution and limitations remain in the project data manifest and model card.

# COMMAND ----------
import base64, csv, io, hashlib, json, re
from datetime import datetime, timezone
from pyspark.sql import functions as F, Window
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
catalog = spark.sql('SELECT current_catalog()').first()[0]
schema = 'fourth_down_portfolio'
assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', catalog), 'Unexpected catalog identifier'
namespace = f'`{catalog}`.`{schema}`'
week, scoring, ppr = 13, 'half', 0.5
spark.sql(f'CREATE SCHEMA IF NOT EXISTS {namespace}')
csv_bytes = base64.b64decode('cGxheWVyX2lkLG5hbWUscG9zaXRpb24sdGVhbSxzZWFzb24sd2VlayxvcHBvbmVudCxzdGFuZGFyZF9wb2ludHMscmVjZXB0aW9ucw0KMDAtMDAyMzQ1OSxBYXJvbiBSb2RnZXJzLFFCLE5ZSiwyMDI0LDMsTkUsMjEuMDQsMA0KMDAtMDAyNjQ5OCxNYXR0aGV3IFN0YWZmb3JkLFFCLExBLDIwMjQsMyxTRiwxMi44NCwwDQowMC0wMDMwMDM1LEFkYW0gVGhpZWxlbixXUixDQVIsMjAyNCwzLExWLDEwLjAsMw0KMDAtMDAzMDA2MSxaYWNoIEVydHosVEUsV0FTLDIwMjQsMyxDSU4sMy44LDUNCjAwLTAwMzA1MDYsVHJhdmlzIEtlbGNlLFRFLEtDLDIwMjQsMyxBVEwsMy4wLDQNCjAwLTAwMzA1NjQsRGVBbmRyZSBIb3BraW5zLFdSLFRFTiwyMDI0LDMsR0IsMTMuMyw2DQowMC0wMDMxMzgxLERhdmFudGUgQWRhbXMsV1IsTFYsMjAyNCwzLENBUiw0LjAsNA0KMDAtMDAzMTQwOCxNaWtlIEV2YW5zLFdSLFRCLDIwMjQsMyxERU4sMS43LDINCjAwLTAwMzI3NjQsRGVycmljayBIZW5yeSxSQixCQUwsMjAyNCwzLERBTCwyOS40LDENCjAwLTAwMzMyOTMsQWFyb24gSm9uZXMsUkIsTUlOLDIwMjQsMyxIT1UsMjAuOCw1DQowMC0wMDMzNTUzLEphbWVzIENvbm5lcixSQixBUkksMjAyNCwzLERFVCwyLjUsMQ0KMDAtMDAzMzkwNixBbHZpbiBLYW1hcmEsUkIsTk8sMjAyNCwzLFBISSwxMi43LDMNCjAwLTAwMjM0NTksQWFyb24gUm9kZ2VycyxRQixOWUosMjAyNCw0LERFTiwxMS42LDANCjAwLTAwMjY0OTgsTWF0dGhldyBTdGFmZm9yZCxRQixMQSwyMDI0LDQsQ0hJLDQuODYsMA0KMDAtMDAzMDA2MSxaYWNoIEVydHosVEUsV0FTLDIwMjQsNCxBUkksNC4yLDMNCjAwLTAwMzAyNzksS2VlbmFuIEFsbGVuLFdSLENISSwyMDI0LDQsTEEsMS45LDMNCjAwLTAwMzA1MDYsVHJhdmlzIEtlbGNlLFRFLEtDLDIwMjQsNCxMQUMsOC45LDcNCjAwLTAwMzA1NjQsRGVBbmRyZSBIb3BraW5zLFdSLFRFTiwyMDI0LDQsTUlBLDMuMSwyDQowMC0wMDMxNDA4LE1pa2UgRXZhbnMsV1IsVEIsMjAyNCw0LFBISSwxNS40LDgNCjAwLTAwMzI3NjQsRGVycmljayBIZW5yeSxSQixCQUwsMjAyNCw0LEJVRiwzMi45LDMNCjAwLTAwMzMyOTMsQWFyb24gSm9uZXMsUkIsTUlOLDIwMjQsNCxHQiwxMy45LDQNCjAwLTAwMzM1NTMsSmFtZXMgQ29ubmVyLFJCLEFSSSwyMDI0LDQsV0FTLDE3LjMsMQ0KMDAtMDAzMzkwNixBbHZpbiBLYW1hcmEsUkIsTk8sMjAyNCw0LEFUTCwxNy45LDcNCjAwLTAwMjM0NTksQWFyb24gUm9kZ2VycyxRQixOWUosMjAyNCw1LE1JTiwxMS43NiwwDQowMC0wMDI2NDk4LE1hdHRoZXcgU3RhZmZvcmQsUUIsTEEsMjAyNCw1LEdCLDEyLjQsMA0KMDAtMDAzMDA2MSxaYWNoIEVydHosVEUsV0FTLDIwMjQsNSxDTEUsMS4wLDINCjAwLTAwMzAyNzksS2VlbmFuIEFsbGVuLFdSLENISSwyMDI0LDUsQ0FSLDMuMywzDQowMC0wMDMwNTA2LFRyYXZpcyBLZWxjZSxURSxLQywyMDI0LDUsTk8sNy4wLDkNCjAwLTAwMzE0MDgsTWlrZSBFdmFucyxXUixUQiwyMDI0LDUsQVRMLDE4LjIsNQ0KMDAtMDAzMjc2NCxEZXJyaWNrIEhlbnJ5LFJCLEJBTCwyMDI0LDUsQ0lOLDE1LjYsMQ0KMDAtMDAzMzI5MyxBYXJvbiBKb25lcyxSQixNSU4sMjAyNCw1LE5ZSiw1LjMsMQ0KMDAtMDAzMzU1MyxKYW1lcyBDb25uZXIsUkIsQVJJLDIwMjQsNSxTRiwxMi4wLDINCjAwLTAwMzM5MDYsQWx2aW4gS2FtYXJhLFJCLE5PLDIwMjQsNSxLQyw2LjYsNg0KMDAtMDAyMzQ1OSxBYXJvbiBSb2RnZXJzLFFCLE5ZSiwyMDI0LDYsQlVGLDE3Ljc2LDANCjAwLTAwMzAwNjEsWmFjaCBFcnR6LFRFLFdBUywyMDI0LDYsQkFMLDYuOCw0DQowMC0wMDMwMjc5LEtlZW5hbiBBbGxlbixXUixDSEksMjAyNCw2LEpBWCwxNi4xLDUNCjAwLTAwMzA1NjQsRGVBbmRyZSBIb3BraW5zLFdSLFRFTiwyMDI0LDYsSU5ELDUuNCw0DQowMC0wMDMxNDA4LE1pa2UgRXZhbnMsV1IsVEIsMjAyNCw2LE5PLDMuNCwyDQowMC0wMDMyNzY0LERlcnJpY2sgSGVucnksUkIsQkFMLDIwMjQsNixXQVMsMjUuMiwwDQowMC0wMDMzNTUzLEphbWVzIENvbm5lcixSQixBUkksMjAyNCw2LEdCLDIuNiw0DQowMC0wMDMzODk3LEpvZSBNaXhvbixSQixIT1UsMjAyNCw2LE5FLDI1LjIsMg0KMDAtMDAzMzkwNixBbHZpbiBLYW1hcmEsUkIsTk8sMjAyNCw2LFRCLDEyLjQsNQ0KMDAtMDAyMzQ1OSxBYXJvbiBSb2RnZXJzLFFCLE5ZSiwyMDI0LDcsUElULDEzLjA0LDANCjAwLTAwMjY0OTgsTWF0dGhldyBTdGFmZm9yZCxRQixMQSwyMDI0LDcsTFYsMy45NiwwDQowMC0wMDMwMDYxLFphY2ggRXJ0eixURSxXQVMsMjAyNCw3LENBUiwxMC4wLDQNCjAwLTAwMzA1MDYsVHJhdmlzIEtlbGNlLFRFLEtDLDIwMjQsNyxTRiwxLjcsNA0KMDAtMDAzMDU2NCxEZUFuZHJlIEhvcGtpbnMsV1IsVEVOLDIwMjQsNyxCVUYsLTAuMiwxDQowMC0wMDMxMzgxLERhdmFudGUgQWRhbXMsV1IsTllKLDIwMjQsNyxQSVQsMy4wLDMNCjAwLTAwMzE0MDgsTWlrZSBFdmFucyxXUixUQiwyMDI0LDcsQkFMLDguNSwxDQowMC0wMDMyNzY0LERlcnJpY2sgSGVucnksUkIsQkFMLDIwMjQsNyxUQiwyNC4yLDENCjAwLTAwMzMyOTMsQWFyb24gSm9uZXMsUkIsTUlOLDIwMjQsNyxERVQsMTcuNiwzDQowMC0wMDMzNTUzLEphbWVzIENvbm5lcixSQixBUkksMjAyNCw3LExBQywxNS4yLDINCjAwLTAwMzM4OTcsSm9lIE1peG9uLFJCLEhPVSwyMDI0LDcsR0IsMjQuNCwyDQowMC0wMDMzOTA2LEFsdmluIEthbWFyYSxSQixOTywyMDI0LDcsREVOLDIuNCw2DQowMC0wMDIzNDU5LEFhcm9uIFJvZGdlcnMsUUIsTllKLDIwMjQsOCxORSwxNy4zMiwwDQowMC0wMDI2NDk4LE1hdHRoZXcgU3RhZmZvcmQsUUIsTEEsMjAyNCw4LE1JTiwyNC43NiwwDQowMC0wMDMwMDYxLFphY2ggRXJ0eixURSxXQVMsMjAyNCw4LENISSw3LjcsNw0KMDAtMDAzMDI3OSxLZWVuYW4gQWxsZW4sV1IsQ0hJLDIwMjQsOCxXQVMsMy45LDINCjAwLTAwMzA1MDYsVHJhdmlzIEtlbGNlLFRFLEtDLDIwMjQsOCxMViwxNS4wLDEwDQowMC0wMDMwNTY0LERlQW5kcmUgSG9wa2lucyxXUixLQywyMDI0LDgsTFYsMi45LDINCjAwLTAwMzEzODEsRGF2YW50ZSBBZGFtcyxXUixOWUosMjAyNCw4LE5FLDUuNCw0DQowMC0wMDMyNzY0LERlcnJpY2sgSGVucnksUkIsQkFMLDIwMjQsOCxDTEUsMTMuNywxDQowMC0wMDMzMjkzLEFhcm9uIEpvbmVzLFJCLE1JTiwyMDI0LDgsTEEsOS41LDINCjAwLTAwMzM1NTMsSmFtZXMgQ29ubmVyLFJCLEFSSSwyMDI0LDgsTUlBLDEyLjksMg0KMDAtMDAzMzg5NyxKb2UgTWl4b24sUkIsSE9VLDIwMjQsOCxJTkQsMTkuNCw0DQowMC0wMDMzOTA2LEFsdmluIEthbWFyYSxSQixOTywyMDI0LDgsTEFDLDEyLjIsNg0KMDAtMDAyMzQ1OSxBYXJvbiBSb2RnZXJzLFFCLE5ZSiwyMDI0LDksSE9VLDIwLjM0LDANCjAwLTAwMjY0OTgsTWF0dGhldyBTdGFmZm9yZCxRQixMQSwyMDI0LDksU0VBLDE3LjkyLDANCjAwLTAwMzAwNjEsWmFjaCBFcnR6LFRFLFdBUywyMDI0LDksTllHLDAuNSwxDQowMC0wMDMwMjc5LEtlZW5hbiBBbGxlbixXUixDSEksMjAyNCw5LEFSSSwzLjYsNA0KMDAtMDAzMDUwNixUcmF2aXMgS2VsY2UsVEUsS0MsMjAyNCw5LFRCLDguMCwxNA0KMDAtMDAzMDU2NCxEZUFuZHJlIEhvcGtpbnMsV1IsS0MsMjAyNCw5LFRCLDIwLjYsOA0KMDAtMDAzMTM4MSxEYXZhbnRlIEFkYW1zLFdSLE5ZSiwyMDI0LDksSE9VLDE1LjEsNw0KMDAtMDAzMjc2NCxEZXJyaWNrIEhlbnJ5LFJCLEJBTCwyMDI0LDksREVOLDI1LjMsMQ0KMDAtMDAzMzI5MyxBYXJvbiBKb25lcyxSQixNSU4sMjAyNCw5LElORCw4LjIsNA0KMDAtMDAzMzU1MyxKYW1lcyBDb25uZXIsUkIsQVJJLDIwMjQsOSxDSEksMTEuOSwzDQowMC0wMDMzODk3LEpvZSBNaXhvbixSQixIT1UsMjAyNCw5LE5ZSiwxNi42LDANCjAwLTAwMzM5MDYsQWx2aW4gS2FtYXJhLFJCLE5PLDIwMjQsOSxDQVIsMjEuNSw2DQowMC0wMDIzNDU5LEFhcm9uIFJvZGdlcnMsUUIsTllKLDIwMjQsMTAsQVJJLDQuMDQsMA0KMDAtMDAyNjQ5OCxNYXR0aGV3IFN0YWZmb3JkLFFCLExBLDIwMjQsMTAsTUlBLDkuNzIsMA0KMDAtMDAzMDA2MSxaYWNoIEVydHosVEUsV0FTLDIwMjQsMTAsUElULDMuMSw0DQowMC0wMDMwMjc5LEtlZW5hbiBBbGxlbixXUixDSEksMjAyNCwxMCxORSw0LjQsNQ0KMDAtMDAzMDUwNixUcmF2aXMgS2VsY2UsVEUsS0MsMjAyNCwxMCxERU4sMTIuNCw4DQowMC0wMDMwNTY0LERlQW5kcmUgSG9wa2lucyxXUixLQywyMDI0LDEwLERFTiw1LjYsNA0KMDAtMDAzMTM4MSxEYXZhbnRlIEFkYW1zLFdSLE5ZSiwyMDI0LDEwLEFSSSwzLjEsNg0KMDAtMDAzMjc2NCxEZXJyaWNrIEhlbnJ5LFJCLEJBTCwyMDI0LDEwLENJTiwxMy4xLDENCjAwLTAwMzMyOTMsQWFyb24gSm9uZXMsUkIsTUlOLDIwMjQsMTAsSkFYLDEwLjEsMg0KMDAtMDAzMzU1MyxKYW1lcyBDb25uZXIsUkIsQVJJLDIwMjQsMTAsTllKLDE3LjMsNQ0KMDAtMDAzMzg5NyxKb2UgTWl4b24sUkIsSE9VLDIwMjQsMTAsREVULDE1LjAsMg0KMDAtMDAzMzkwNixBbHZpbiBLYW1hcmEsUkIsTk8sMjAyNCwxMCxBVEwsMTAuOSw1DQowMC0wMDIzNDU5LEFhcm9uIFJvZGdlcnMsUUIsTllKLDIwMjQsMTEsSU5ELDE2LjA2LDANCjAwLTAwMjY0OTgsTWF0dGhldyBTdGFmZm9yZCxRQixMQSwyMDI0LDExLE5FLDI3LjgsMA0KMDAtMDAzMDA2MSxaYWNoIEVydHosVEUsV0FTLDIwMjQsMTEsUEhJLDEyLjcsNg0KMDAtMDAzMDI3OSxLZWVuYW4gQWxsZW4sV1IsQ0hJLDIwMjQsMTEsR0IsNC4xLDQNCjAwLTAwMzA1MDYsVHJhdmlzIEtlbGNlLFRFLEtDLDIwMjQsMTEsQlVGLDAuOCwyDQowMC0wMDMwNTY0LERlQW5kcmUgSG9wa2lucyxXUixLQywyMDI0LDExLEJVRiwyLjksMw0KMDAtMDAzMTM4MSxEYXZhbnRlIEFkYW1zLFdSLE5ZSiwyMDI0LDExLElORCw3LjIsNg0KMDAtMDAzMjc2NCxEZXJyaWNrIEhlbnJ5LFJCLEJBTCwyMDI0LDExLFBJVCwxMC41LDANCjAwLTAwMzMyOTMsQWFyb24gSm9uZXMsUkIsTUlOLDIwMjQsMTEsVEVOLDQuMywxDQowMC0wMDMzODk3LEpvZSBNaXhvbixSQixIT1UsMjAyNCwxMSxEQUwsMzMuMywyDQowMC0wMDMzOTA2LEFsdmluIEthbWFyYSxSQixOTywyMDI0LDExLENMRSw4LjksNA0KMDAtMDAyNjQ5OCxNYXR0aGV3IFN0YWZmb3JkLFFCLExBLDIwMjQsMTIsUEhJLDE5LjIyLDANCjAwLTAwMzAwMzUsQWRhbSBUaGllbGVuLFdSLENBUiwyMDI0LDEyLEtDLDUuNywzDQowMC0wMDMwMDYxLFphY2ggRXJ0eixURSxXQVMsMjAyNCwxMixEQUwsOS44LDYNCjAwLTAwMzAyNzksS2VlbmFuIEFsbGVuLFdSLENISSwyMDI0LDEyLE1JTiwxNC42LDkNCjAwLTAwMzA1MDYsVHJhdmlzIEtlbGNlLFRFLEtDLDIwMjQsMTIsQ0FSLDYuMiw2DQowMC0wMDMwNTY0LERlQW5kcmUgSG9wa2lucyxXUixLQywyMDI0LDEyLENBUiw5LjUsNQ0KMDAtMDAzMTQwOCxNaWtlIEV2YW5zLFdSLFRCLDIwMjQsMTIsTllHLDYuOCw1DQowMC0wMDMyNzY0LERlcnJpY2sgSGVucnksUkIsQkFMLDIwMjQsMTIsTEFDLDE0LjAsMA0KMDAtMDAzMzI5MyxBYXJvbiBKb25lcyxSQixNSU4sMjAyNCwxMixDSEksMTYuOSwzDQowMC0wMDMzNTUzLEphbWVzIENvbm5lcixSQixBUkksMjAyNCwxMixTRUEsNC45LDUNCjAwLTAwMzM4OTcsSm9lIE1peG9uLFJCLEhPVSwyMDI0LDEyLFRFTiw0LjUsNQ0KMDAtMDAyMzQ1OSxBYXJvbiBSb2RnZXJzLFFCLE5ZSiwyMDI0LDEzLFNFQSwxNC4wLDANCjAwLTAwMjY0OTgsTWF0dGhldyBTdGFmZm9yZCxRQixMQSwyMDI0LDEzLE5PLDE1LjYyLDANCjAwLTAwMzAwMzUsQWRhbSBUaGllbGVuLFdSLENBUiwyMDI0LDEzLFRCLDE1LjksOA0KMDAtMDAzMDA2MSxaYWNoIEVydHosVEUsV0FTLDIwMjQsMTMsVEVOLDkuNSwzDQowMC0wMDMwMjc5LEtlZW5hbiBBbGxlbixXUixDSEksMjAyNCwxMyxERVQsMTkuMyw1DQowMC0wMDMwNTA2LFRyYXZpcyBLZWxjZSxURSxLQywyMDI0LDEzLExWLDYuOCw3DQowMC0wMDMwNTY0LERlQW5kcmUgSG9wa2lucyxXUixLQywyMDI0LDEzLExWLDkuMCw0DQowMC0wMDMxMzgxLERhdmFudGUgQWRhbXMsV1IsTllKLDIwMjQsMTMsU0VBLDEyLjYsNQ0KMDAtMDAzMTQwOCxNaWtlIEV2YW5zLFdSLFRCLDIwMjQsMTMsQ0FSLDE3LjgsOA0KMDAtMDAzMjc2NCxEZXJyaWNrIEhlbnJ5LFJCLEJBTCwyMDI0LDEzLFBISSwxMS4xLDMNCjAwLTAwMzMyOTMsQWFyb24gSm9uZXMsUkIsTUlOLDIwMjQsMTMsQVJJLDYuOCwzDQowMC0wMDMzNTUzLEphbWVzIENvbm5lcixSQixBUkksMjAyNCwxMyxNSU4sOC4xLDMNCjAwLTAwMzM4OTcsSm9lIE1peG9uLFJCLEhPVSwyMDI0LDEzLEpBWCwxNy45LDQNCjAwLTAwMzM5MDYsQWx2aW4gS2FtYXJhLFJCLE5PLDIwMjQsMTMsTEEsMTEuOSw0DQowMC0wMDIzNDU5LEFhcm9uIFJvZGdlcnMsUUIsTllKLDIwMjQsMTQsTUlBLDE3LjU2LDANCjAwLTAwMjY0OTgsTWF0dGhldyBTdGFmZm9yZCxRQixMQSwyMDI0LDE0LEJVRiwyMC44LDANCjAwLTAwMzAwMzUsQWRhbSBUaGllbGVuLFdSLENBUiwyMDI0LDE0LFBISSwxMC4yLDkNCjAwLTAwMzAyNzksS2VlbmFuIEFsbGVuLFdSLENISSwyMDI0LDE0LFNGLDMuMCwzDQowMC0wMDMwNTA2LFRyYXZpcyBLZWxjZSxURSxLQywyMDI0LDE0LExBQyw0LjUsNQ0KMDAtMDAzMDU2NCxEZUFuZHJlIEhvcGtpbnMsV1IsS0MsMjAyNCwxNCxMQUMsOS4yLDQNCjAwLTAwMzEzODEsRGF2YW50ZSBBZGFtcyxXUixOWUosMjAyNCwxNCxNSUEsMTYuOSw5DQowMC0wMDMxNDA4LE1pa2UgRXZhbnMsV1IsVEIsMjAyNCwxNCxMViw2LjksNA0KMDAtMDAzMzI5MyxBYXJvbiBKb25lcyxSQixNSU4sMjAyNCwxNCxBVEwsMTQuNCwyDQowMC0wMDMzNTUzLEphbWVzIENvbm5lcixSQixBUkksMjAyNCwxNCxTRUEsMTguMiw0DQowMC0wMDMzOTA2LEFsdmluIEthbWFyYSxSQixOTywyMDI0LDE0LE5ZRyw3LjksNQ0KMDAtMDAyMzQ1OSxBYXJvbiBSb2RnZXJzLFFCLE5ZSiwyMDI0LDE1LEpBWCwzMC4wNiwwDQowMC0wMDI2NDk4LE1hdHRoZXcgU3RhZmZvcmQsUUIsTEEsMjAyNCwxNSxTRiw4LjIsMA0KMDAtMDAzMDAzNSxBZGFtIFRoaWVsZW4sV1IsQ0FSLDIwMjQsMTUsREFMLDUuMSw1DQowMC0wMDMwMDYxLFphY2ggRXJ0eixURSxXQVMsMjAyNCwxNSxOTywyLjUsMg0KMDAtMDAzMDI3OSxLZWVuYW4gQWxsZW4sV1IsQ0hJLDIwMjQsMTUsTUlOLDE0LjIsNg0KMDAtMDAzMDUwNixUcmF2aXMgS2VsY2UsVEUsS0MsMjAyNCwxNSxDTEUsMi43LDQNCjAwLTAwMzA1NjQsRGVBbmRyZSBIb3BraW5zLFdSLEtDLDIwMjQsMTUsQ0xFLDMuNiw1DQowMC0wMDMxMzgxLERhdmFudGUgQWRhbXMsV1IsTllKLDIwMjQsMTUsSkFYLDMzLjgsOQ0KMDAtMDAzMTQwOCxNaWtlIEV2YW5zLFdSLFRCLDIwMjQsMTUsTEFDLDI3LjksOQ0KMDAtMDAzMjc2NCxEZXJyaWNrIEhlbnJ5LFJCLEJBTCwyMDI0LDE1LE5ZRyw2LjcsMA0KMDAtMDAzMzI5MyxBYXJvbiBKb25lcyxSQixNSU4sMjAyNCwxNSxDSEksMTYuNiwyDQowMC0wMDMzNTUzLEphbWVzIENvbm5lcixSQixBUkksMjAyNCwxNSxORSwyNS44LDUNCjAwLTAwMzM4OTcsSm9lIE1peG9uLFJCLEhPVSwyMDI0LDE1LE1JQSw1LjYsNQ0KMDAtMDAzMzkwNixBbHZpbiBLYW1hcmEsUkIsTk8sMjAyNCwxNSxXQVMsMTMuMCw0DQowMC0wMDIzNDU5LEFhcm9uIFJvZGdlcnMsUUIsTllKLDIwMjQsMTYsTEEsMTIuODQsMA0KMDAtMDAyNjQ5OCxNYXR0aGV3IFN0YWZmb3JkLFFCLExBLDIwMjQsMTYsTllKLDYuMCwwDQowMC0wMDMwMDM1LEFkYW0gVGhpZWxlbixXUixDQVIsMjAyNCwxNixBUkksMTAuMyw1DQowMC0wMDMwMDYxLFphY2ggRXJ0eixURSxXQVMsMjAyNCwxNixQSEksMS4yLDENCjAwLTAwMzAyNzksS2VlbmFuIEFsbGVuLFdSLENISSwyMDI0LDE2LERFVCwyMC4xLDkNCjAwLTAwMzA1MDYsVHJhdmlzIEtlbGNlLFRFLEtDLDIwMjQsMTYsSE9VLDMuMCw1DQowMC0wMDMwNTY0LERlQW5kcmUgSG9wa2lucyxXUixLQywyMDI0LDE2LEhPVSwzLjcsNA0KMDAtMDAzMTM4MSxEYXZhbnRlIEFkYW1zLFdSLE5ZSiwyMDI0LDE2LExBLDEyLjgsNw0KMDAtMDAzMTQwOCxNaWtlIEV2YW5zLFdSLFRCLDIwMjQsMTYsREFMLDYuOSw1DQowMC0wMDMyNzY0LERlcnJpY2sgSGVucnksUkIsQkFMLDIwMjQsMTYsUElULDE4LjksMg0KMDAtMDAzMzI5MyxBYXJvbiBKb25lcyxSQixNSU4sMjAyNCwxNixTRUEsOS4zLDMNCjAwLTAwMzM1NTMsSmFtZXMgQ29ubmVyLFJCLEFSSSwyMDI0LDE2LENBUiwyMi42LDQNCjAwLTAwMzM4OTcsSm9lIE1peG9uLFJCLEhPVSwyMDI0LDE2LEtDLDcuMSwxDQo=')
assert hashlib.sha256(csv_bytes).hexdigest() == '6c23d4c0e85077f2cc31fed03117f75517a6790dbc4bb1796f37bbf8e5d4f4eb'
parsed_rows = list(csv.DictReader(io.StringIO(csv_bytes.decode('utf-8'))))
for row in parsed_rows:
    for field in ('season','week','receptions'):
        row[field] = int(row[field])
    row['standard_points'] = float(row['standard_points'])
assert len(parsed_rows) == 164

# COMMAND ----------
contract = StructType([
    StructField('player_id', StringType(), False), StructField('name', StringType(), False),
    StructField('position', StringType(), False), StructField('team', StringType(), False),
    StructField('season', IntegerType(), False), StructField('week', IntegerType(), False),
    StructField('opponent', StringType(), False), StructField('standard_points', DoubleType(), False),
    StructField('receptions', IntegerType(), False)
])
# FAILFAST rejects malformed rows. Explicit null checks below are still necessary with CSV input.
raw = spark.createDataFrame(parsed_rows, schema=contract)
for field in contract.fieldNames():
    assert raw.filter(F.col(field).isNull()).limit(1).count() == 0, f'Null in {field}'
assert raw.limit(1).count() > 0, 'Empty source'
invalid = raw.filter(
    (~F.col('position').isin('QB','RB','WR','TE')) |
    (~F.col('week').between(1,18)) | (F.col('season') != 2024) |
    (~F.col('standard_points').between(-100,150)) | F.isnan('standard_points') |
    (~F.col('receptions').between(0,50)) |
    (~F.col('player_id').rlike('^[A-Za-z0-9_-]{1,50}$')) |
    (~F.col('team').rlike('^[A-Z]{2,4}$')) | (~F.col('opponent').rlike('^[A-Z]{2,4}$')) |
    (~F.length(F.col('name')).between(1,100))
)
assert invalid.limit(1).count() == 0, 'Source failed the data contract'
assert raw.groupBy('player_id','season','week').count().filter('count > 1').limit(1).count() == 0, 'Duplicate player-week key'
assert raw.groupBy('player_id').agg(F.countDistinct('position').alias('positions')).filter('positions > 1').limit(1).count() == 0, 'Resolve position changes explicitly'
raw.write.format('delta').mode('overwrite').option('overwriteSchema','true').saveAsTable(f'{catalog}.{schema}.player_games')

# COMMAND ----------
# Crucial: exclude the target/future weeks BEFORE all window functions.
history = raw.filter((F.col('season')==2024) & (F.col('week')<week)).withColumn('points',F.col('standard_points')+F.lit(ppr)*F.col('receptions'))
by_player = Window.partitionBy('player_id','season')
newest = by_player.orderBy(F.col('week').desc())
ranked = history.withColumn('history_mean',F.avg('points').over(by_player)).withColumn('history_count',F.count('*').over(by_player)).withColumn('recency_rank',F.row_number().over(newest))
recent = ranked.filter(F.col('recency_rank')<=6).withColumn('weight',F.pow(F.lit(0.75),F.col('recency_rank')-1))
summary = recent.groupBy('player_id','season').agg(
    (F.sum(F.col('points')*F.col('weight'))/F.sum('weight')).alias('recent_weighted'),
    F.stddev_pop('points').alias('volatility'),
    F.first('history_mean').alias('history_mean'), F.first('history_count').alias('history_count'))
latest = ranked.filter(F.col('recency_rank')==1).select('player_id','season','name','team','position',F.col('week').alias('history_end'))
gold = summary.join(latest,['player_id','season']).withColumn('projection',F.lit(0.65)*F.col('recent_weighted')+F.lit(0.35)*F.col('history_mean')).withColumn('decision_week',F.lit(week)).withColumn('scoring',F.lit(scoring))
assert gold.filter(F.col('history_end')>=F.col('decision_week')).limit(1).count()==0, 'Temporal leakage'
# Eligibility is intentionally left to the local app (bye map + manual exclusions + history rules).
# This batch table is a projection artifact, NOT an automatically eligible lineup.
gold.write.format('delta').mode('overwrite').option('overwriteSchema','true').saveAsTable(f'{catalog}.{schema}.projections')
display(gold.orderBy(F.col('projection').desc()))


# COMMAND ----------
# Verify table readback and agreement with the independently run local implementation.
expected = {'00-0033897': {'projection': 19.5078, 'baseline': 20.9857, 'recent_weighted': 18.712, 'volatility': 8.4861, 'n': 7, 'last_week': 12}, '00-0026498': {'projection': 17.4218, 'baseline': 14.8311, 'recent_weighted': 18.8169, 'volatility': 8.2194, 'n': 9, 'last_week': 12}, '00-0032764': {'projection': 17.3292, 'baseline': 20.84, 'recent_weighted': 15.4387, 'volatility': 5.8775, 'n': 10, 'last_week': 12}, '00-0023459': {'projection': 14.2994, 'baseline': 14.7733, 'recent_weighted': 14.0442, 'volatility': 5.264, 'n': 9, 'last_week': 11}, '00-0033906': {'projection': 14.2063, 'baseline': 14.3889, 'recent_weighted': 14.108, 'volatility': 5.7215, 'n': 9, 'last_week': 11}, '00-0033293': {'projection': 12.6184, 'baseline': 13.2333, 'recent_weighted': 12.2873, 'volatility': 4.9795, 'n': 9, 'last_week': 12}, '00-0033553': {'projection': 12.5196, 'baseline': 12.1222, 'recent_weighted': 12.7335, 'volatility': 5.1341, 'n': 9, 'last_week': 12}, '00-0031408': {'projection': 10.5493, 'baseline': 10.9167, 'recent_weighted': 10.3516, 'volatility': 6.8793, 'n': 6, 'last_week': 12}, '00-0030506': {'projection': 10.2791, 'baseline': 10.5556, 'recent_weighted': 10.1303, 'volatility': 6.6749, 'n': 9, 'last_week': 12}, '00-0030279': {'projection': 10.1297, 'baseline': 8.675, 'recent_weighted': 10.913, 'volatility': 6.1471, 'n': 8, 'last_week': 12}, '00-0030061': {'projection': 9.593, 'baseline': 8.06, 'recent_weighted': 10.4185, 'volatility': 4.9996, 'n': 10, 'last_week': 12}, '00-0030564': {'projection': 9.3137, 'baseline': 8.9556, 'recent_weighted': 9.5065, 'volatility': 7.9261, 'n': 9, 'last_week': 12}, '00-0031381': {'projection': 9.2491, 'baseline': 8.8, 'recent_weighted': 9.4909, 'volatility': 4.7184, 'n': 6, 'last_week': 11}, '00-0030035': {'projection': 9.1504, 'baseline': 9.35, 'recent_weighted': 9.0429, 'volatility': 2.15, 'n': 2, 'last_week': 12}}
saved = spark.table(f'{catalog}.{schema}.projections')
rows = [r.asDict() for r in saved.collect()]
assert len(rows) == len(expected) == 14
assert {r['player_id'] for r in rows} == set(expected)
comparisons = {'projection':'projection', 'history_mean':'baseline', 'recent_weighted':'recent_weighted', 'volatility':'volatility'}
max_error = 0.0
for row in rows:
    ref = expected[row['player_id']]
    for cloud_name, local_name in comparisons.items():
        difference = abs(row[cloud_name] - ref[local_name])
        assert difference <= 0.000051, (row['player_id'], cloud_name, difference)
        max_error = max(max_error, difference)
    assert row['history_count'] == ref['n']
    assert row['history_end'] == ref['last_week']
assert spark.table(f'{catalog}.{schema}.player_games').count() == 164
verification = {
    'status': 'PASS', 'executed_at_utc': datetime.now(timezone.utc).isoformat(),
    'source_records': 164, 'forecast_rows': 14, 'season': 2024,
    'decision_week': week, 'scoring': scoring,
    'source_sha256': hashlib.sha256(csv_bytes).hexdigest(),
    'max_absolute_difference_from_local_rounded_values': max_error,
    'tables': [f'{catalog}.{schema}.player_games', f'{catalog}.{schema}.projections'],
    'databricks_executed': True, 'direct_s3_read': False,
    'source_transfer': 'Embedded exact copy of the separately uploaded AWS S3 object',
    's3_uri': 's3://fourth-down-adam-skarre-20261006/player_games.csv'
}
print(json.dumps(verification, indent=2))
payload = json.dumps({'verification': verification, 'projections': rows}, indent=2, allow_nan=False).encode()
encoded = base64.b64encode(payload).decode()
displayHTML(f'<h3>PASS — 164 records and 14 forecasts verified</h3><p>Both Delta tables were read back successfully. All four forecast statistics agree with local results within rounding tolerance.</p><a download="fourth_down_databricks_results.json" href="data:application/json;base64,{encoded}">Download verified results</a>')
