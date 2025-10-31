# How To Use The Code #

// Used Library \\
== External Library == 
1. pygame
== Internal Library ==
1. **heapq**: Digunakan untuk implementasi algoritma pathfinding A* (sebagai priority queue).
2. **sys**: Digunakan untuk keluar dari aplikasi secara bersih (sys.exit).
3. **random**: Digunakan untuk memilih map secara acak dan beberapa logika gerakan hantu.
4. **time**: Digunakan untuk mengatur durasi mode (Frightened, Scatter, Chase) dan timer.

// IDE Version \\
== IDE ==
1. Visual Studio Code (VS Code)
2. PyCharm
== Version ==
[ no specified vers to use ]

// Installation \\
### Langkah 1: Install Python
Pastikan Python 3 sudah ter-install di komputer Anda.
1.  Kunjungi situs resmi Python: `https://www.python.org/downloads/`
2.  Download installer untuk sistem operasi Anda (Windows/Mac/Linux).
3.  Jalankan installer.
4.  **PENTING:** Saat instalasi, pastikan Anda mencentang kotak yang bertuliskan "Add Python to PATH" atau "Add python.exe to PATH" sebelum mengklik "Install Now".

### Langkah 2: Install Library 'pygame'
Satu-satunya library eksternal yang perlu Anda install adalah `pygame`.
1.  Buka Terminal (di Mac/Linux) atau Command Prompt / PowerShell (di Windows).
2.  Ketikkan perintah berikut dan tekan Enter:
    ```
    pip install pygame
    ```
3.  Tunggu beberapa saat hingga proses download dan instalasi selesai.

### Langkah 3: Menjalankan Source Code
Setelah Python dan pygame ter-install, Anda bisa menjalankan game.
1.  Simpan source code di atas sebagai file bernama `pacman.py`.
2.  Buka Terminal / Command Prompt Anda.
3.  Pindah direktori (menggunakan perintah `cd`) ke folder tempat Anda menyimpan file `pacman.py`.
    Contoh:
    `cd C:\Users\NamaAnda\Documents\ProjectPacman`
4.  Setelah berada di direktori yang benar, ketik perintah berikut untuk menjalankan game:
    ```
    python pacman.py
    ```
    (Jika perintah di atas gagal, coba gunakan `python3 pacman.py`)
5.  Jendela game Pac-Man akan otomatis terbuka. Gunakan tombol panah (Arrow Keys) untuk mulai bermain. Tekan 'ESC' untuk keluar.
---------------------------------
