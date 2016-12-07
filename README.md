# SolarwindsServiceCheck

Bu scriptler Solarwinds sisteminin kontrol edemediği uygulamaları ve özel olarak kontrol edilmek istenen sistemlerden rahatca veri çekilebilmesi için tasarlanmıştır.Şuanda Couchbase, RabbitMq, Elasticsearch ve GoogleAnalytics sistemlerini kontrol etmektedir.Scriptlerin detaylı açıklamaları aşağıda ayrı ayrı verilmiştir.

# Tüm Scriptler İçin Ortak Kütüphane ve Dosyalar

## Config.cfg

Config dosyası içerisinde tüm alanlar ayrılmış birer bölümden oluşmaktadır.Buradaki tüm bölümlerin açıklaması dosya içerisinde mevcuttur.Fakat yinede aşağıda açıklanacaktır.İlerleyen versiyonlarda config dosyaları merkezi hale getirilecektir.Şuan için tüm uygulamaların ayrı ayrı config dosyaları bulunmaktadır.

  + [log] alanı: Bu alanda sistemin loglarını atacağı path verilmelidir.Log dosyası kendiliğinden oluşacaktır.İlerleyen versiyonlarda log rotate fonksyonu da getirilecektir.
  + [contact] alanı: Bu alanda alarmların gideceği mail ve member grupları belirlenir.Henüz bu bölümdeki multi mail özelliği aktif değildir.İstenirse oluşabilecek alarmlar tek bir gruba yada mail adresine gönderilebilir.
  + [env] alanı: Bu alan ana ayarların yer aldığı alandır.Eklenen her bir uygulama bölümü, bu alanda yer alan "system_members" anahtarına karşılık olarak virgülle ayrılmış biçimde eklenmelidir.
  + [mail] alanı: Bu alan mail sunucu ayarlarını içeren bölümdür.
  + Uygulama bölümü : Bu alanın örnek tanımı aşağıda verilmiştir.Ayrıntılar buradan incelenebilir.

```
[section_name]
cpass = [couchbase_password]
cuser = [couchbase_user]
server = [server_name]
table = [mysql_table_name]
default_bucket = [bucket_name]
```

## LogMaster

Scriptlerin içinde gerçekleşen olayları loglamak için yazılmış basit bir kütüphanedir.Config dosyasında [log] alanında belirtilen klasöre dosyaları yazar.Eğer klasör yoksa kendisi oluşturur.İlerleyen zamanlarda logrotate de eklenecektir.Log formatı "[timestamp] [service_name] [level] [message]" şeklindedir.Örnek log;

``` [Thu, 15 Sep 2016 19:27:19] [REST SERVICE] [ACCESS] [172.--.---.-- , sysroot , /sys/api/v0.1/dmall_rabbitmq/queuestats ,RESPONSE:200 OK
] ```

## Db

Scriptlerin ürettiği dataları, kritik bazı olayları ve uygulamalar arasında saklanması gereken herşeyi yazmak, okumak ve toplam kayıtlarını listelemek için basit bir kütüphanedir.İlgili tablolar arasındaki işlemler bu kütüphane sayesinde yapılır.Sıradaki versiyonda db kullanıcı adı, şifresi ve database ismi de config dosyasına taşınacaktır.

## SendMail

Scriptlerde meydana gelebilecek aksaklıklar ve önemli alarmlar için önceden yazılmış bir kütüphanedir.Arada bu tarz olayları kontrol edecek başka bir uygulama varsa (bizim konumuzda bu solarwinds olacak) bu kütüphaneye ihtiyacınız olmayabilir.Ancak ilerleyen versiyonlarda scriptlerin bilinmeyen çökme durumlarında ilgililere mail attırılıcağı için yinede konfigüre etmekte fayda var.Config dosyasında [mail] alanı ayarlanarak kütüphane kullanılabilir.Script, gmail sunucularına göre (ssl gerekliliği vs.) ayarlanmıştır.Eğer mail sunucu ayarlarınız bunlardan farklıysa script içinden değiştirmeniz gerekiyor.

# Kontrol Edilen Uygulamalar ve Kontrol scriptleri

Scriptler, config dosyasında belirtilen 1 veya daha fazla couchbase sistemine rest servisi üzerinden bağlanarak istenilen dataları alır ve ilgili mysql tablosuna yazdırır.İhtiyaçlar doğrultusunda kullanım ve kontrol alanı daha da geliştirilebilecek olan bu  scriptler çok daha değişik kontrol metodlarını kullanabilirler.İlerleyen versiyonlarda çok daha değişik kontrol merodlarına yer vereceğiz.Eğer config dosyasında ilgili alanda belirtilen tablo yer almıyorsa kendisi bu tabloyu oluşturu ve kayıt işlemine devam eder.Hangi sunucu kümesi için işlem yaptığının ayırt edilebilmesi için log dosyasında parantez içinde config dosyasına yazdığınız alan ismi yazılır.

## CouchWatcher (Couchbase)

Bucket flushlamak için gerekli olan modül de yazılmış ve scripte eklenmiştir.İstenilmesi halinde aktif edilebilir.

### Toplanan Datalar

+ Sunuculara ait datalar
  + Hostname (String)
  + Status (String)
  + Uptime (Integer)
  + Cluster Membership (String)
  + Memory Total (Integer)
  + Memory Used (Integer)
  + Swap Total (Integer)
  + Swap Used (Integer)
  + CPU Utilizations (Float)
  + Cluster Count (Integer)
  + Bucket Count (Integer)
  + Bucket Stats (Dict)
+ Bucketlara ait datalar
  + Item Count (Integer)
+ Clustera ait datalar
  + Cluster HDD Stats (Dict)
  + Cluster RAM Stats (Dict)

## RabbitMqWatcher (RabbitMQ)

### Toplanan Datalar

+ Sunuculara ait datalar
  + Address (String)
  + Status (String)
  + Cluster Membership (String)
  + Running (Bool)
  + Uptime (Integer)
  + Disk Free (Integer)
  + Disk Free Alarm (Integer)
  + Disk Free Limit (Integer)
  + Memory Used (Integer)
  + Memory Alarm (Integer)
  + Memory Limit (Integer)
  + File Descriptor Total (Integer)
  + File Descriptor Used (Integer)
  + Socket Total (Integer)
  + Socket Used (Integer)
+ Queuelara ait datalar
  + Name (String)
  + Status (String)
  + State (String)
  + Consumers (Integer)
  + Sync Slave Nodes (Comma delimited string)
  + Msg Unacked (Integer)
  + Msg Ready (Integer)
  + Master Node (String)
  + Disk Reads (Integer)
  + Disk Write (Integer)
  + Deliver Get (Float)
  + Publish Get (Float)

## ElasticsearchWatcher (Elasticsearch with kopf plugin)

### Toplanan Datalar

+ Sunuculara ait datalar
  + Host Unique Name (Unique hash for each host/instance)
  + Target Env (String)
  + Hostname (String)
  + Is Master (Bool)
  + Uptime (Integer)
  + Load Avg (Semicolon delimited float)
  + Physical Memory Free Percent (Integer)
  + Physical Memory Usage Percent (Integer)
  + Swap Used (Float)
  + Swap Free (Float)
  + CPU Usage Percent (Integer)
  + JVM Uptime (Integer)
  + JVM Heap Max (Float)
  + JVM Heap Usage Percent (Integer)
  + JVM Thread Count (Integer)
  + JVM Thread Peak Count (Integer)
+ Clustera ait datalar
  + Number of Data Source (Integer)
  + Number of Nodes (Integer)
  + Cluster Status (String)
  + Cluster Name (String)
+ Genel datalar
  + Total Shards (Integer)
  + Successful Shards (Integer)
  + Docs Total (Integer)
  + Docs Deleted (Integer)

## GoogleAnalytics

Bu modülü kullanabilmek için öncelikle "client_secrets.json" adındaki, api login bilgilerinizi içeren dosyayı google api yönetim konsolundan indirip, "/Service/GoogleAnalytics" klasörüne atmalı ve scripti bir defa elle tetikleyerek erişime izin vermelisiniz.Sonrasında script işlemleri kendisi halledecektir.

### Toplanan Datalar

+ All Application Data Metric (All device and platform)
