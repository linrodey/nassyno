# Chạy nền tảng kết nối

Python 3.12; chạy từ checkout hiện có, không cần worktree. Không chạy public ở giai đoạn này.

```bash
cd /workspace/nassyno
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp config.example.json config.local.json
```

Sửa `config.local.json` bằng endpoint thật trước khi probe. File ví dụ chỉ dùng domain `.invalid`, không phải thiết bị thật. Có thể thêm `ca_file` trỏ tới file CA đáng tin cậy ở ngoài Git. CA cần thiết là public certificate, không phải private key.

Khởi động local (khóa ứng dụng được sinh trong bộ nhớ shell, không in giá trị):

```bash
export NAS_MANAGER_CONFIG="$PWD/config.local.json"
export NAS_MANAGER_ADMIN_TOKEN="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))')"
.venv/bin/python -m uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8080
```

Mở giao diện tại địa chỉ máy phát triển tương ứng khi chạy ở máy của bạn; lấy khóa ứng dụng qua secret manager hoặc cơ chế nhập an toàn của hệ thống triển khai, không đưa khóa lên chat. Có thể cấp khóa qua biến môi trường thay vì lệnh sinh tạm. Không dùng mật khẩu NAS thay khóa ứng dụng. Cách sinh tạm ở trên phục vụ API/kiểm thử nội bộ; trang console cần cùng khóa được cấp an toàn cho người vận hành.

Trong môi trường cloud hiện tại chỉ dùng yêu cầu local để kiểm tra, chưa công bố URL truy cập bên ngoài.

## Kiểm thử

```bash
python3 -m unittest discover -s tests -v
node --test prototype/model.test.cjs
node --check web/app.js
```

Các dependencies trực tiếp đã ghim phiên bản; chưa có lockfile toàn bộ dependencies bắc cầu. Cần khóa đầy đủ và kiểm tra ảnh container trước bước triển khai production.

## Kết quả hiện tại

10 kiểm thử backend đạt: cấu hình sai, địa chỉ không hợp lệ, khóa ứng dụng, inventory, API discovery chỉ đọc, phản hồi sai/quá lớn, redirect, timeout/TLS/proxy, không lộ lỗi nhạy cảm và health. 4 kiểm thử logic prototype đạt. Backend được khởi động thực tế và kiểm tra console bằng Chromium trong môi trường cloud. Tất cả phản hồi DSM trong kiểm thử backend đều là mock; chưa có phiên xác thực NAS thật.

Bước 2 còn mở: nhận endpoint NAS thử nghiệm và tuyến mạng, đối chiếu tài liệu DSM, kiểm tra TLS/API thật, rồi bổ sung cơ chế đăng nhập/phiên và quyền tối thiểu. Chưa chuyển sang các chức năng ghi của Bước 4–6.
