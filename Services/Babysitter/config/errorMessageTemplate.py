#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Message(object):
    def itemcount(self, server, hware, actdate, severity):
        subject = """ {0} Couchbase server, {1} donanımı {2} eşik seviyesine ulaştı. """.format(server, hware, severity)
        body = """
			Sayın İlgili;
		
				{0} Hostname / IP Couchbase serverınıza ait {1} değeri, {2} tarihinde
            {3} eşik değerini aşmıştır.Sistemlerinizin kesintiye uğdamamsı için lütfen sunucunuzu 
            kontrol ediniz."config.cfg" dosyasında "mustflash" parametresi "True" olarak ayarlanmışsa,
			eşik değeri "Error" sınırına ulaşınca "Bucket" flashlanacaktır.

											CouchWatcher
				""".format(server, hware, actdate, severity)
        return body, subject

    def general(self, server, hware, actdate, severity):
        subject = """ {0} Couchbase server, {1} donanımı {2} eşik seviyesine ulaştı. """.format(server, hware, severity)
        body = """
			Sayın İlgili;
	
				{0} Hostname / IP Couchbase serverınıza ait {1} donanımınız, {2} tarihinde
			{3} eşik değerini aşmıştır.Sistemlerinizin kesintiye uğdamamsı için lütfen sunucunuzu 
			kontrol ediniz.
	
											CouchWatcher
				""".format(server, hware, actdate, severity)
        return body, subject

    def unreachable(self, servers):
        subject = """ Cluster ve Main Server ulaşılamaz durumda !!!! """
        body = """
			Sayın İlgili;

				Cluster yapınız içerisinde bulunan sunuculara ve "MainServer" olarak tanımladığınız sunucuya ulaşılamıyor.lütfen
			sistemlerinizi kontrol ediniz.Sunucuların listesi aşağıda yer almaktadır.

				{0}

											CouchWatcher
				""".format(servers)
        return body, subject

    def noClusterMember(self):
        subject = """ Main Server ulaşılamaz durumda ve Cluster bulunmuyor. !!!! """
        body = """
			Sayın İlgili;

				"MainServer" parametresinde yer alan sunucu şuanda ulaşılamaz durumda.Cluster yapınızda sunucu yer almadığı
			için şuan sistemleriniz erişilemez durumda.Lütfen sistemlerinizi kontrol ediniz.

											CouchWatcher
				"""
        return body, subject
