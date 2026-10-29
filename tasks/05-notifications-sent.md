# 05 — notifications_sent

## რას ვაკეთებთ

ვიმახსოვრებთ, რომელ მოწყობილობას რომელ მიწისძვრაზე გაეგზავნა შეტყობინება, რომ იგივე წყვილი მეორედ აღარ გავიდეს.

## როგორ

პირველადი გასაღები `(event_id, device_id)` ბაზის დონეზე კრძალავს დუბლიკატს. `event_id` არის endpoint-ის `event.id`, ჩვეულებრივი `integer`, გარე გასაღების გარეშე.

გაგზავნამდე ვწერთ ჩანაწერს და Expo-ს მხოლოდ მაშინ ვეძახით, თუ სტრიქონი ახლა ჩაიწერა:

```sql
INSERT INTO notifications_sent (event_id, device_id, status)
VALUES (:event_id, :device_id, 'pending')
ON CONFLICT (event_id, device_id) DO NOTHING
RETURNING event_id;
```

`RETURNING` ცარიელია — ეს წყვილი უკვე გაგზავნილია ან გაგზავნა უკვე დაწყებულია, მეორედ აღარ ვაგზავნით.

ჯერ ვარჩევთ ვის უნდა გაეგზავნოს, და მხოლოდ ამ მოწყობილობებზე ვაკეთებთ `INSERT`-ს.

მიწისძვრას ვკითხულობთ `GET https://iesdata.iliauni.edu.ge:3030/api/publish_events/`-იდან და ვიღებთ `items[].event`-ს. `items[].id` გამოქვეყნების ჩანაწერია და აქ არ გამოიყენება. სიაში მოხვედრა ნიშნავს, რომ მიწისძვრა უკვე გამოქვეყნებულია. მოწყობილობა კანდიდატია, თუ:

1. მაგნიტუდა (`event.magnitudes`, ჯერ `ML`) ფარავს `alert_settings.min_magnitude`-ს.
2. `event.latitude` / `event.longitude` ხვდება `alert_settings.area`-ში და `enabled` ჭეშმარიტია.
3. `devices.push_token` შევსებულია.

ამ კანდიდატზე ჩაწერა თუ მოხერხდა, ვაგზავნით. წარმატებაზე ვინახავთ `expo_ticket_id`-ს და `status = 'ok'`. Expo-ს შეცდომაზე სტრიქონი რჩება `status = 'error'` და მიზეზით `error`-ში, რომ იგივე წყვილი თავიდან არ გაიგზავნოს.

`expo_ticket_id` რამდენიმე წუთში Expo-ს receipt-ის შესამოწმებლად გვჭირდება. თუ receipt აბრუნებს `DeviceNotRegistered`, ამ მოწყობილობის `push_token` ვაცარიელებთ.

## მზადაა, როცა

იგივე `(event_id, device_id)` მეორედ აღარ იგზავნება, და გაგზავნა იწყება მხოლოდ მაშინ, როცა `INSERT ... ON CONFLICT DO NOTHING` სტრიქონს რეალურად ქმნის.
