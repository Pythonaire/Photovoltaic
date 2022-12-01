# Photovoltaic RTC 6000

Implement a photovoltaic system (inclusive battery) into homekit, with fakegato-history.

## python packages needed:
- HAP-Python --> pip3 install HAP-python[QRCode]
- sqlite3 --> sudo apt install sqlite3
- rtcclient --> sudo pip3 install -U rctclient

To present historical data (ex. year household energy consumption) two routine are used:
I had some trouble to call data from the photovoltaic directly via rtcclient api (connection error), so the solution for me is catching the data along a databaase cache. This is a good way, because data presented from the photovoltaic is limited.

### FillDatabase: 

  * FillDatabase.py read photovoltaic values via rtcclient and store them into a local database.
It is called by a cron job each 5 minutes.

```python
sudo crontab -u root -e 
*/5 * * * * /usr/bin/python3 /your file location/FillDatabase.py >> /var/log/syslog 2>&1
  ````
Instead of simple 'crontab - e' use this to route FillDatabase messages through cron into syslog. Don´t forget to make FillDatabase.py executable: 'sudo chmod 777 /your file location/FillDatabase.py'.

### CacheData.py
  * CacheData read the values from the database and store them into a dictionary. This because, i use sqlite3 as database.

### sqlite3:

```sql
sqlite3 'your database'

CREATE TABLE 'RTC' (id INTEGER PRIMARY KEY NOT NULL, time INTEGER NOT NULL, PanelCurrentConsumption FLOAT DEFAULT 0 NOT NULL, PanelTotalConsumption FLOAT DEFAULT 0 NOT NULL, FeedCurrentConsumption FLOAT DEFAULT 0 NOT NULL, FeedTotalConsumption FLOAT DEFAULT 0 NOT NULL, GridCurrentConsumption FLOAT DEFAULT 0 NOT NULL, GridTotalConsumption FLOAT DEFAULT 0 NOT NULL, HouseholdCurrentConsumption FLOAT DEFAULT 0 NOT NULL, HouseholdTotalConsumption FLOAT DEFAULT 0 NOT NULL, BatteryCurrentConsumption FLOAT DEFAULT 0 NOT NULL, BatteryTotalConsumption FLOAT DEFAULT 0 NOT NULL, BatteryPercentage INTEGER DEFAULT 0 NOT NULL, BatteryState INTEGER DEFAULT 0 NOT NULL);

.quit
````



At least: 

  * Change database location and photovoltaic device address in config.py
  * start main.py and authorize the bridge into apple homekit

To present historical data history.py or history310.py is called, related to you python minor version, because Python 3.10 contains faster match function.

