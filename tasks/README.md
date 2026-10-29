# აპის ცხრილები

ამ ბაზაში მხოლოდ აპის ოთხი ცხრილია: `devices`, `alert_settings`, `felt_reports`, `notifications_sent`. მიწისძვრების ცხრილები აქ არ იქმნება და გარე გასაღებით არ უკავშირდება.

გამოქვეყნებული მიწისძვრა უკვე აწყობილია [iesdata](https://iesdata.iliauni.edu.ge:3030/en/)-ზე. ინფორმაციას ვკითხულობთ საკუთარი endpoint-იდან:

`GET https://iesdata.iliauni.edu.ge:3030/api/publish_events/`

პასუხში `items[]`-ის თითო ელემენტს აქვს `id` (გამოქვეყნების ჩანაწერი) და `event` (თავად მიწისძვრა). აპი და ეს ცხრილები იყენებენ `event.id`-ს. ეს რიცხვი იწერება `felt_reports.event_id`-სა და `notifications_sent.event_id`-ში, უბრალო `integer`-ად, `REFERENCES`-ის გარეშე.

მაგნიტუდა, დრო და კოორდინატები იმავე `event`-იდან მოდის. მაგნიტუდა ჯერ `ML`-ია, თუ არ არის — პირველი შევსებული მნიშვნელობა. სიაში მხოლოდ გამოქვეყნებული მიწისძვრებია.

## რიგი

1. [01 — PostGIS და ოთხი ცხრილი](01-schema.md)
2. [02 — devices](02-devices.md)
3. [03 — alert_settings](03-alert-settings.md)
4. [04 — felt_reports](04-felt-reports.md)
5. [05 — notifications_sent](05-notifications-sent.md)

