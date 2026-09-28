# P-3D Demo Assets

## 方針

P-3Dの初回表示とデモ切替で使用する、完全オリジナルの生成画像である。既存作品、商標、実在人物を参照せず、文字、ロゴ、透かしを含めない。P-3Dの疑似立体表示で前景・中景・背景を認識しやすい縦長構図とし、完成絵、背景、透過立ち絵の3ファイルを1セットとする。

生成日: 2026-09-28  
生成手段: OpenAI組み込み画像生成機能（新規生成と参照画像編集）  
生成元: 1024x1536 PNG  
配信用: 完成絵／背景は1024x1536 JPEG品質86、透過立ち絵は1024x1536 RGBA PNG

## 生成プロンプト

### 激烈ゆるキャラ

```text
P-3D vertical demo artwork. Create an explosively cute, completely original mochi-like yuru-chara with a clear rounded silhouette, tiny limbs, sparkling eyes, soft blush and plush 3D texture. Place the full body centered at about 60% of the vertical frame in a pastel layered garden, with blurred foreground flowers, a readable midground path and distant dreamy foliage. Add warm golden rim light and gentle contact shadow so the subject separates cleanly for depth effects. Stylized concept art, joyful, wholesome, premium character design. No text, logo, watermark, existing franchise resemblance, copyrighted character, or trademark.
```

### 美少女キャラ

```text
P-3D vertical demo illustration. Create a completely original, clearly adult woman in her twenties with silver-lavender hair, emerald eyes and a tasteful teal-and-cream fantasy cafe outfit. Show a centered three-quarter body composition occupying about 65% of the frame in a luminous greenhouse cafe. Separate the scene into foreground leaves and glass highlights, a sharply readable character midground, and distant tables, windows and sky for strong parallax. Use a refined high-end anime illustration style, elegant pose, soft cinematic light, controlled rim light and natural contact shadow. Wholesome and non-sexualized. No text, logo, watermark, real-person likeness, existing franchise resemblance, copyrighted character, or trademark.
```

### モフモフ動物

```text
P-3D vertical demo artwork. Create a completely original small fantasy animal combining the gentle appeal of a red panda and a Pomeranian without copying any known mascot. Give it extremely fluffy copper-and-cream fur, oversized expressive eyes, tiny paws and a magnificent soft tail. Place the full body centered at about 60% of the frame in an autumn forest with blurred foreground leaves, a mossy midground and distant layered trees. Use cinematic storybook lighting, bright fur rim light, soft contact shadow and a crisp readable silhouette for depth separation. Adorable, wholesome, premium stylized concept art. No text, logo, watermark, existing franchise resemblance, copyrighted character, or trademark.
```

## 2層化の編集プロンプト

各完成絵を参照画像として、次の2系統をキャラクターごとに実行した。

### 透過立ち絵

```text
Edit this exact original artwork into a production-ready transparent character standee for a layered parallax demo. Isolate only the central subject and retain its complete silhouette, fine hair or fur, accessories and rim-lit edge. Remove every part of the environment, foreground, ground and contact shadow. Preserve the subject's design, expression, pose, colors, proportions, placement, scale, lighting, detail and 2:3 canvas alignment from the reference. Use transparent pixels everywhere else with clean softly antialiased alpha edges and no colored halo. No added elements, text, logo, border, checkerboard, matte or watermark.
```

個別指定は、ゆるキャラでは耳・葉・花・鈴・手足、美少女では髪・顔・手・衣装・装飾・スカート・脚、モフモフ動物では耳・顔・手足・尻尾・ひげ・細い毛先までを保持対象に含めた。

### 背景プレート

```text
Edit this exact original artwork into the clean background plate for a layered parallax scene. Completely remove the central subject, its accessories, rim-light halo, contact shadow and any subject-shaped residue. Reconstruct all hidden scenery naturally with coherent perspective, color, lighting and depth. Preserve the original 2:3 canvas, camera angle, framing, palette, illumination, foreground blur and scenery outside the removed subject. The center must contain only believable empty scenery ready for a separate transparent character layer. No character, person, animal, creature, silhouette, text, logo, border or watermark.
```

個別指定は、ゆるキャラでは庭園の石畳・花・橋・木・空・家、美少女ではテーブル・椅子・温室・植物・噴水・城景、モフモフ動物では苔・岩・小川・滝・落葉・木・木漏れ日を背景復元対象に含めた。

## 配信ファイル

|ファイル|SHA-256|
|---|---|
|`assets/demos/demo-mascot.jpg`|`a3cc1eb2c0e23aeb3e6ef7fc744df520f72fa0a5ed0b7483a3ebd2ddea31cfaf`|
|`assets/demos/demo-mascot-background.jpg`|`b574b7732280b51063c87a5d7a04cc5c2aa710ceab6b9ec26e7cd57dcc11bc5b`|
|`assets/demos/demo-mascot-foreground.png`|`740dd41726f7c2cf097b251f9b092e6e070f15cdd45fbe623afc7ce99ad5585b`|
|`assets/demos/demo-heroine.jpg`|`306faab43094ffc18921e1faf9fc33b7915ca2d36898dc75ff67d518660214d5`|
|`assets/demos/demo-heroine-background.jpg`|`8e2b18ba7c907bd44341b4614f12fb7eeec9de7cc5c509339cb2ac8153a71c21`|
|`assets/demos/demo-heroine-foreground.png`|`cf2244c706e838f3d7c98284062cf036aa19e9735111b51b6cc68daec3b8acaa`|
|`assets/demos/demo-fluffy.jpg`|`e95fa6d388242d45fad3b5ce3cdac3df608f132c9a470cd05c218672366626b6`|
|`assets/demos/demo-fluffy-background.jpg`|`6395283c0ab4e6f5ba4c5525ffae42345eeb97f3631315949a07b55975a257f9`|
|`assets/demos/demo-fluffy-foreground.png`|`1064fb3cf7a0e37552ff01b367870b8baad5e39904b81e5b62ba1798afed311f`|

生成元PNGは配信サイズとリポジトリ容量を抑えるため公開リポジトリへ含めない。配信素材は同一オリジンから読み込み、利用者の端末画像やカメラ画像と同様にブラウザ内でWebGL処理する。透過立ち絵のalphaは人物／物体マスクとしても利用する。
