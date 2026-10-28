# Gói khảo sát chỉ đọc cho phiên GPT Công việc

Phạm vi được duyệt: tiếp tục Bước 2, khảo sát NAS SITE qua phiên đã đăng nhập được, chuẩn bị backend thử nghiệm. Chưa duyệt chuyển sang thao tác ghi hoặc mở production. Phiên hiện tại không thể điều khiển hay lấy cookie của một phiên GPT khác; người dùng chuyển đoạn yêu cầu bên dưới sang phiên đó rồi mang kết quả đã lọc về.

## Đoạn yêu cầu để chuyển sang phiên đã đăng nhập

```text
Hãy khảo sát CHỈ ĐỌC NAS Synology tại https://nassite.hbcg.vn:5001 để chuẩn bị ứng dụng quản trị nhiều NAS (repo linrodey/nassyno).

Dùng phiên đăng nhập được phép hiện có, kiểm tra đúng hostname/TLS. Nếu có skill hbcg-synology-nas, đọc SKILL.md và baseline/operations trước khảo sát; baseline chỉ là lịch sử, không thay trạng thái hiện tại. Model trong hồ sơ là RS2423RP+II, phải xác minh trên UI chứ không suy ra từ tên.

Không thay đổi NAS: không Apply/Save/OK cấu hình, không bật SSH/SNMP/API, không cài gói/nâng DSM, không khởi động lại, không chạy SMART/scrub/repair, không tạo User/Group, không áp ACL, không ngắt phiên hoặc sửa firewall. Đóng hộp cấu hình bằng Cancel. Không chấp nhận thông báo tự mở cổng. Chờ bảng tải xong, không coi Loading hoặc thiếu quyền là không có dữ liệu.

Không xuất mật khẩu/OTP/cookie/SID/SynoToken/Authorization header/private key, support bundle hay nội dung tài liệu doanh nghiệp. Không copy request/response đăng nhập, HAR, console dump hoặc toàn bộ cấu hình LDAP/Portal. Chỉ tổng hợp metadata cần thiết, dùng bí danh cho người dùng/nhóm/thư mục/IP ngoài endpoint đã được cấp. Không xuất toàn bộ danh sách file hoặc tài khoản.

Khảo sát theo từng mục, ghi thời điểm GMT+7 và đường dẫn UI bằng chứng:
1. Info Center: model, bản DSM đầy đủ, uptime, trạng thái tham gia domain/LDAP (không ghi credential).
2. Resource Monitor: CPU/RAM, giao diện mạng, đơn vị lưu lượng, khả năng xem phiên người dùng. Chỉ xem, không ngắt phiên.
3. Storage Manager: số khay/enclosure, HDD/SSD và trạng thái, nhiệt độ; trang SMART gần nhất và khả năng hiển thị; tuổi thọ SSD nếu có. Không chạy kiểm tra mới. Dùng alias ổ thay serial thật trong báo cáo chia sẻ.
4. Quan hệ ổ → Pool → Volume: RAID/SHR, thành viên/Hot Spare, trạng thái/rebuild, Btrfs/ext4 và dung lượng có nhãn rõ lớp/đơn vị. Không cộng vật lý, Pool, Volume. Ghi SSD Cache và LUN/Target nếu có; không cài SAN Manager nếu chưa có.
5. File Station: xác nhận mở được và xem metadata của đúng một thư mục thử nghiệm được người quản trị chỉ định. Nếu chưa có thư mục được chỉ định, chỉ xem danh sách share, chưa mở tài liệu. Không tải hoặc mở nội dung file.
6. User & Group: tổng số và phân loại local/domain/LDAP nếu UI cung cấp; khả năng xem thành viên nhóm, không ghi tên thật hoặc hashes. Không tạo tài khoản.
7. Quyền: dùng thư mục thử nghiệm được chỉ định; xem quyền share, ACL trực tiếp/kế thừa và nhóm. Nếu chưa có thư mục thử nghiệm, đánh dấu chưa kiểm tra. Không suy ra quyền hiệu lực chỉ từ một ACE, không áp đệ quy.
8. Security/Firewall: xem có bật không, profile/interface, cách thể hiện thứ tự luật; tổng hợp số luật thay vì xuất địa chỉ/mạng chi tiết. Không sửa hoặc thử chặn IP.
9. External Access/Login Portal/Reverse Proxy: xác nhận đường HTTPS hiện tại, QuickConnect bật/chưa kiểm tra, không xuất ID nếu chưa được phép; ghi khả năng truy cập, không đổi cấu hình. Không kết luận QuickConnect hỗ trợ API backend chỉ từ trang DSM mở được.
10. Directory Services/SNMP/SSO: chỉ ghi loại tích hợp và trạng thái hiện có, không xuất bind DN/credential, community hay auth/privacy key; không bật dịch vụ mới.

Với mỗi mục ghi một trong: observed / not_found / not_checked / blocked, UI path, kết quả tóm tắt và giới hạn. not_found chỉ khi đã mở đúng trang, đủ quyền và dữ liệu tải xong. UI hiển thị chức năng không chứng minh API backend được hỗ trợ. Tách đề xuất khỏi hiện trạng. Nếu thiếu quyền hoặc thông tin, dừng mục đó, tiếp tục các mục độc lập.

Trả báo cáo Markdown đã lọc bí mật; nếu có mẫu survey/template.json từ repo thì trả thêm JSON đúng mẫu, giữ source_type=operator_ui_report. Chưa kiểm tra thì giữ null/not_checked, không điền dữ liệu minh họa thành dữ liệu thật. Cuối báo cáo ghi: có thay đổi gì không, mục nào chưa kiểm tra và cần gì để tiếp tục. Chỉ logout nếu phiên do bạn tự tạo và việc đó không đóng phiên người dùng đang sử dụng; không xuất phiên đăng nhập để chuyển sang GPT khác.
```

## Nhận kết quả

Người dùng dán báo cáo đã lọc hoặc đính kèm JSON, không đưa credential vào báo cáo. Dữ liệu này được đánh dấu **báo cáo UI do người vận hành cung cấp**, chưa phải bằng chứng backend đã kết nối. Không mở rộng quyền NAS từ kết quả nhập báo cáo.

Mẫu `survey/template.json` chưa có kết quả thật. Kiểm tra bằng `python3 -m backend.survey_report <file.json>` trên môi trường GPT; người dùng không cần Python. Trình kiểm tra không sửa NAS và không lưu báo cáo vào Git. Nội dung tự do vẫn cần người vận hành rà soát bí mật; schema không phải bộ lọc dữ liệu nhạy cảm hoàn hảo.

## Chuẩn bị máy chủ thử nghiệm song song

Chưa triển khai lên Windows của người dùng. Chọn hostname ứng dụng, chứng chỉ HTTPS, máy chủ/VM/container host và IP đầu ra cố định; endpoint NAS đã có. Cần quyền triển khai được cấp qua cơ chế an toàn, không qua chat. Chỉ khi máy chủ đã có mới kiểm tra đường mạng, trusted proxy, kho credential, SSO/RBAC, audit và login/logout thật từ backend.

Docker local đã có để thử trên Windows 10/11 có Docker Desktop nhưng người dùng không muốn cài thêm ở máy cá nhân; đây không còn là yêu cầu bắt buộc. Không coi gói local là môi trường production đã sẵn sàng. Nếu máy chủ là Windows Server, đánh giá Linux VM hoặc host Linux được quản lý thay vì mặc định cài Docker Desktop.

## Điểm duyệt tiếp theo

Sau khi có báo cáo: đối chiếu model/DSM/storage, cập nhật ma trận khả năng, chọn NAS/thư mục/tài khoản thử nghiệm và trình bày phần cần kiểm chứng trực tiếp. Chỉ chuyển sang bước giám sát/File Station read-only sau khi có bằng chứng backend đăng nhập, đọc, logout trên NAS thật và người dùng duyệt kết quả Bước 2. Không kiểm thử ghi trên SITE đang vận hành.
