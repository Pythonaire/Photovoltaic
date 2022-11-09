# Photovoltaic RTC 6000

Implement a photovoltaic system (inclusive battery) into homekit, with fakegato-history.

![Title](image.jpg "Title")


python packages needed:
- HAP-Python --> pip3 install HAP-python[QRCode]
- sqlite3 --> sudo apt install sqlite3
- rtcclient --> sudo pip3 install -U rctclient

To present historical data (ex. year household energy consumption) two routine are used:

FillDatabase: 

  * FillDatabase.py read photovoltaic values via rtcclient and store them into a local database.
It is called by a cron job each 5 minutes.

```python
sudo crontab -u root -e 
*/5 * * * * /usr/bin/python3 /your file location/FillDatabase.py >> /var/log/syslog 2>&1
  ````
  * (instead of simple crontab - e use this to route FillDatabase messages through cron into syslog)
  
  * don't forget to make FillDatabase.py executable: sudo chmod 777 /your file location/FillDatabase.py



RTCExchange.py read the values from the database an store them into a dictionary. This because, i use sqlite3 as database. It seems to me, sqlite3 couldn't used under threading conditions.

sqlite3:

CREATE TABLE 'RTC' (id INTEGER PRIMARY KEY NOT NULL, time INTEGER NOT NULL, PanelCurrentConsumption FLOAT DEFAULT 0 NOT NULL, PanelTotalConsumption FLOAT DEFAULT 0 NOT NULL, FeedCurrentConsumption FLOAT DEFAULT 0 NOT NULL, FeedTotalConsumption FLOAT DEFAULT 0 NOT NULL, GridCurrentConsumption FLOAT DEFAULT 0 NOT NULL, GridTotalConsumption FLOAT DEFAULT 0 NOT NULL, HouseholdCurrentConsumption FLOAT DEFAULT 0 NOT NULL, HouseholdTotalConsumption FLOAT DEFAULT 0 NOT NULL, BatteryCurrentConsumption FLOAT DEFAULT 0 NOT NULL, BatteryTotalConsumption FLOAT DEFAULT 0 NOT NULL, BatteryPercentage INTEGER DEFAULT 0 NOT NULL, BatteryState INTEGER DEFAULT 0 NOT NULL);

Change database location and photovoltaic device address in config.py

