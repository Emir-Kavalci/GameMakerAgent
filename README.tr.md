# GameMakerAgent

[English](README.md) | **Türkçe**

**Unreal Engine 5** ile tek başına oyun yapanlar için bir [Claude Code](https://code.claude.com) agent ekibi.

Gerçek bir oyun stüdyosunda programcılar, tasarımcılar, sanatçılar, test uzmanları ve yapımcılar vardır. Tek başına geliştirici bunların hepsi olmak zorundadır. GameMakerAgent, Claude Code'a oyun geliştirmedeki her rol için bir agent verir; böylece her işi o konunun uzmanına devredebilirsiniz.

> **Durum: erken önizleme (v0.8.0).** Windows üzerinde Unreal Engine 5.7 için yapıldı. Temel özellik akışı (tasarımcı, programcı, QA, yapımcı) gerçek bir Unreal Engine 5.7 C++ projesinde baştan sona denendi ve her agent'ın otomatik davranış testleri var (bkz. [TESTING.md](TESTING.md), İngilizce). Pürüzler olabilir.

## Neler var

### Agent'lar

**Çekirdek ekip: oyunu yapar**

| Agent | Görevi |
| --- | --- |
| `game-designer` | Fikrinizi şekillendirir, Oyun Tasarım Belgesini (`Docs/GDD.md`) tutar ve her özellik için kabul kriterleri olan bir spec yazar. Kod yazmaz. |
| `level-designer` | Her seviyeyi `Docs/Levels/` içinde planlar; zıplama boşluklarını ve yükseklikleri karakterinizin gerçek hareket değerlerinden hesaplar. (Her script için onayınızla) açık editörde gri kutu taslağını (blockout) kurar. |
| `ui-ux-designer` | Ekranlarınızı ve aralarındaki akışı `Docs/UI.md` içinde planlar (menüler, duraklatma, HUD): metin tel kafes çizimleri, gamepad ile gezinme ve okunabilirlik kuralları. Sonra programcının yapabileceği bir spec yazar. Kod yazmaz. |
| `programmer` | Spec'e göre Unreal Engine C++ oynanış kodunu yazar ve düzeltir, derleme hatalarını açıklar, projenizin kurallarına uyar. |
| `qa` | Kod değişikliklerini spec'e ve sık yapılan Unreal hatalarına göre inceler, elle test planı yazar. Sadece okur: sorunları bildirir ama dosyalarınızı asla değiştirmez. |
| `producer` | Oyunu `Docs/Tasks.md` içinde küçük görevlere böler, her görevi doğru ekip arkadaşına verir ve kapsamı daraltmanıza yardım eder. |

Kodu yazan agent, o kodu inceleyen agent asla değildir.

**Prodüksiyon ve çıkış: sanatı, sesi ve tanıtımı planlar**

| Agent | Görevi |
| --- | --- |
| `art-director` | Görsel stili belirler (`Docs/ArtBible.md`), gereken her sanat varlığını listeler (`Docs/AssetList.md`), sanatçılar veya görsel üretim araçları için brief ve prompt yazar, ekran görüntülerinizi değerlendirir. |
| `technical-artist` | İsimlendirme kuralları, klasör yapısı, poligon ve doku bütçeleri, içe aktarma ve materyal kurulumu, Content klasörü denetimleri, Unreal Editor Python / Blender scriptleri. |
| `audio-director` | Ses efektlerini ve müziği planlar (`Docs/AudioList.md`), ses için brief ve prompt yazar, seslerin Unreal'da nasıl kurulacağını anlatır. |
| `marketing` | `Docs/Marketing/` içinde mağaza sayfası metni, fragman çekim listesi, geliştirme günlükleri (devlog), basın kiti ve çıkış planı. Sadece oyununuzda gerçekten olanları söyler ve kendisi hiçbir şey yayınlamaz. |

**Bu agent'ların yapamadıkları:** Claude görsel, 3D model, müzik veya ses dosyası üretmez. Bu agent'lar planlar, tarif eder, seçtiğiniz kişiler veya araçlar için brief ve prompt yazar, script yazar ve sonuçları değerlendirir.

### Skill'ler (slash komutları)

| Komut | Ne yapar |
| --- | --- |
| `/game-maker-agent:gma-start` | Bu işlerde yeni misiniz? Adım adım bir rehber: bilgisayarınızı kontrol eder (Unreal Engine, Visual Studio C++, Git), bir Unreal projesi oluşturmanıza yardım eder, kurulumda size yol gösterir, ekibi tanıtır ve ilk küçük özelliği birlikte yaparsınız. Nerede kaldığınızı hatırlar (`Docs/GettingStarted.md`); devam etmek için tekrar çalıştırın. |
| `/game-maker-agent:gma-init` | Unreal projenizin içinde bir kez çalıştırın. `CLAUDE.md`, `Docs/GDD.md`, `Docs/Tasks.md` dosyalarını ve (kabul ederseniz) Unreal'a uygun `.gitignore` ve `.gitattributes` dosyalarını ve Unreal Editor bağlantısını kurar. |
| `/game-maker-agent:new-feature <fikir>` | Bir özelliği fikirden incelenmiş koda kadar götürür: spec → kod → derleme (siz editörü kapalı tutarken Claude çalıştırır) → QA incelemesi → sizin editörde testiniz → görev listesinin güncellenmesi. Her adımı siz onaylarsınız. |

Agent'lar ve skill'ler İngilizce yazılmıştır ama onlarla Türkçe konuşabilirsiniz; size Türkçe cevap verirler.

### Unreal Editor bağlantısı (isteğe bağlı, Windows)

GameMakerAgent açık Unreal Editor'ünüze bağlanabilir. O zaman agent'lar tahmin etmek yerine gerçek projeye bakabilir: bir Blueprint'in varsayılan değerlerini veya sahneye yerleştirilmiş bir aktörün değerlerini okur (korumalı C++ özellikleri ve Character Movement gibi bir bileşenin içindeki değerler dahil), varlıkları gerçek türleriyle listeler, açık seviyedeki aktörleri listeler, oynadıktan sonra Output Log'u okur, seviyenin veya oynarken oyunun ekran görüntüsünü alır. Her script için onayınızla bir şeyleri güvenli yoldan, editör üzerinden de değiştirebilirler (örneğin bir Blueprint değerini ayarlamak veya referansları bozmadan varlıkları yeniden adlandırmak).

**Agent'lar sadece C++ kodunuzu değil, Blueprint'lerinizi de okur.** `unreal_read_blueprint` bir Blueprint'i (Actor, Widget veya Anim Blueprint) okunabilir metne çevirir: üst sınıfı, bileşenleri, varsayılan değerleriyle değişkenleri ve her grafiği girintili adımlar olarak. C++'tan gelenleri işaretler: C++'ta tanımlanmış event'ler ve Blueprint'in çağırdığı C++ fonksiyonları gibi. Böylece `programmer` bir C++ sınıfını değiştirmeden önce onun üzerine kurulu Blueprint'leri okur; kullandıkları node'ları bozmaz ve Blueprint'te zaten olan bir mantığı tekrar yazmaz. Örnek çıktı:

```text
Parent class: CoinBase (C++ in this project: /Script/MyGame.CoinBase)

== Event Graph ==
Event OnCollected [event declared in C++] (Collector: Actor)
  Branch(Condition = CoinValue > 10.0)
    True:
      // Give the reward
      CoinBase.AddScore [C++](Amount = 5)
```

Bağlantı Blueprint grafiklerini okur ama node eklemez veya bağlantılarını değiştirmez; bir Blueprint mantık değişikliği için agent o mantığı (kabul ederseniz) C++'a taşır ya da hangi node'ları değiştirmeniz gerektiğini söyler.

**Agent'lar oynadığınızda ne olduğunu görür.** Editörde test ettikten sonra `unreal_read_log`, son Play'den bu yana Output Log'u okur: "Accessed None" gibi hatalar, Blueprint hataları ve sizin kendi log satırlarınız; tekrarlar katlanır, motorun ağ gürültüsü gizlenir. Log dosyasını okuduğu için editör kapandıktan veya çöktükten sonra da çalışır. `unreal_take_screenshot` agent'a seviyenin (veya oynarken arayüzüyle birlikte oyun görüntüsünün) bir resmini verir; böylece `programmer`, `qa`, `technical-artist`, `art-director`, `level-designer` ve `ui-ux-designer` bir değişikliğin nasıl göründüğünü kontrol edebilir. Tek bir aktöre bakabilir ve sizin kameranız hiç oynamaz. Editörün sadece açık olması yeterli: başka pencerelerin arkasında kalabilir. Resim agent'a gider ve hemen silinir; projenize hiçbir şey kaydedilmez.

- **Açmak için:** `/game-maker-agent:gma-init` çalıştırın ve editör bağlantısına evet deyin. Unreal'ın yerleşik Python Editor Script Plugin'ini ve onun "Enable Remote Execution" ayarını açar. Ya da kendiniz yapın: Edit > Plugins > "Python Editor Script Plugin", sonra Edit > Project Settings > Plugins > Python > "Enable Remote Execution?".
- **Kontrol etmek için:** editör açıkken Claude'a *"Unreal Editor bağlı mı?"* diye sorun.
- **Kurulacak bir şey yok:** bağlantı, Unreal Engine'in içinde gelen Python ile çalışır ve Epic'in kendi uzaktan çalıştırma özelliğini kullanır. Sadece kendi bilgisayarınızda dinler (127.0.0.1).
- **Kontrol sizde:** Claude Code, salt okunur araçlar (`unreal_status`, `unreal_list_assets`, `unreal_list_level_actors`, `unreal_get_properties`, `unreal_read_blueprint`, `unreal_read_log`, `unreal_take_screenshot`) çalışmadan önce size sorar; her araç için bir kez "Yes, and don't ask again" derseniz o projede okumalar için artık sormaz. Projeyi değiştirebilecek her script önce size gösterilir ve her seferinde onayınızı ister.
- macOS ve Linux'ta bağlantı henüz desteklenmiyor; Claude Code onu başlatılamayan bir sunucu olarak gösterir. Plugin'in geri kalanı çalışır.

### Güvenlik koruması

Bir Unreal projesinin içinde (`.uproject` dosyası olan bir klasörde) plugin, Claude'un yapmak üzere olduğu her dosya düzenlemesini ve kabuk komutunu kontrol eder:

- `.uasset` ve `.umap` dosyalarında metin düzenlemesini engeller. Bunlar ikili (binary) dosyalardır ve metin olarak düzenlemek onları bozar. Claude bunun yerine editörde yapılacak adımları anlatır.
- Unreal Engine kurulum klasöründeki dosyalarda değişikliği engeller.
- Dosya silen veya değişiklikleri atan bir komuttan önce (`rm`, `del`, `Remove-Item`, `git clean`, `git reset --hard` ve benzerleri), Claude'un komutları sormadan çalıştırmasına izin vermiş olsanız bile her zaman size sorar.
- Unreal Editor içinde bir Python scripti çalışmadan önce her zaman size sorar.

Diğer klasörlerde sadece editör scripti kuralı geçerlidir. Windows'ta Git Bash gerekir; o da [Git for Windows](https://git-scm.com/downloads/win) ile gelir. Git Bash yoksa koruma çalışamaz ve Claude Code bunun yerine bir hook hatası gösterir.

Planlananlar: daha fazla rol ve iş akışı, daha sonra başka motorlar (Unity, Godot).

## Kurulum

[Claude Code](https://code.claude.com) kurulu olmalı.

Bir Claude Code oturumunda şunları çalıştırın:

```
/plugin marketplace add Emir-Kavalci/GameMakerAgent
/plugin install game-maker-agent@game-maker-agent
```

Kurduktan sonra Claude Code'u yeniden başlatın.

Daha sonra güncellemek için `/plugin marketplace update game-maker-agent`, ardından `/plugin update game-maker-agent@game-maker-agent` çalıştırın ve Claude Code'u yeniden başlatın. Nelerin değiştiğini [değişiklik günlüğünde](CHANGELOG.md) (İngilizce) görebilirsiniz.

## Maliyet

GameMakerAgent ücretsiz ve açık kaynaktır. Ücretli bir sürümü, API anahtarı veya kendine ait bir hesap sistemi yoktur.

Agent'lar Claude Code içinde çalıştığı için kullanımları, diğer her Claude Code sohbeti gibi kendi Claude planınızın kullanımından sayılır. Plugin ek bir ücret getirmez.

## Hızlı başlangıç

Daha önce hiç Unreal Engine veya oyun için Claude Code kullanmadınız mı? `claude`'u Unreal projenizin klasöründe (henüz projeniz yoksa boş bir klasörde) başlatın ve `/game-maker-agent:gma-start` çalıştırın; aşağıdakilerin hepsinde size adım adım yol gösterir.

1. Unreal projenizin klasöründe (`.uproject` dosyasının olduğu klasör) bir terminal açın ve `claude`'u başlatın.
2. `/game-maker-agent:gma-init` çalıştırın ve oyununuzla ilgili sorusunu cevaplayın.
3. İlk özelliğinizi yapın: `/game-maker-agent:new-feature koşma yeteneği`
4. Ya da bir ekip arkadaşıyla doğrudan konuşun, örneğin: *"İlk oynanabilir sürüm hedefimi planlamak için producer agent'ını kullan."*

## Geri bildirim ve katkı

Bir agent yanlış bir şey mi yaptı? [Bir issue açın](https://github.com/Emir-Kavalci/GameMakerAgent/issues/new/choose) ve ne istediğinizi, ne olduğunu yazın (Türkçe yazabilirsiniz); agent'ların gelişmesinin ana yolu bu bildirimlerdir. Plugin'i kendiniz değiştirmek için [CONTRIBUTING.md](CONTRIBUTING.md) (İngilizce) dosyasına bakın. Güvenlik sorunları herkese açık issue'lardan değil, [SECURITY.md](SECURITY.md) üzerinden bildirilir.

## Yapay zekâ ile yapıldı

GameMakerAgent yapay zekâ yardımıyla geliştiriliyor: plugin dosyaları, agent talimatları ve belgeler [Claude Code](https://code.claude.com) ile birlikte yazılıyor. Her değişiklik yayınlanmadan önce proje sahibi tarafından gözden geçirilir ve test edilir.

## Sorumluluk reddi

GameMakerAgent bağımsız bir topluluk projesidir. Anthropic veya Epic Games tarafından yapılmamış, onaylanmamış veya desteklenmemektedir. "Unreal Engine", Epic Games, Inc.'in ticari markasıdır. "Claude", Anthropic, PBC'nin ticari markasıdır.

## Lisans

[MIT](LICENSE)
