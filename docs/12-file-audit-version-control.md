# Module File Audit & Version Control — Đặc tả bổ sung

Trạng thái: **ĐÃ BỔ SUNG VÀO PHẠM VI; CHƯA TRIỂN KHAI / CHƯA XÁC MINH NAS THẬT**. Ngày 29/10/2026.
Áp dụng cho ứng dụng quản trị nhiều Synology NAS `linrodey/nassyno`; không nhầm với audit hành động của chính ứng dụng (AuditEvent hiện có).

## Mục tiêu
- Trả lời: tài khoản nào đã tạo, ghi/chỉnh sửa, đổi tên, di chuyển, xóa file/thư mục; vào lúc nào; trên NAS/share/đường dẫn nào; nguồn IP và giao thức nào (nếu nguồn có).
- Tra cứu lịch sử phiên bản và khôi phục bản cũ **chỉ khi nguồn có versioning/snapshot hợp lệ**, phải có duyệt và xác nhận tác động trước ghi.
- So sánh nội dung thay đổi giữa hai phiên bản Word/Excel ở giai đoạn sau; không đồng nhất dấu hiệu write SMB/WebDAV với việc thay đổi một ô/đoạn văn cụ thể.
- Hỗ trợ phân vùng công trình `1.WRK` và `2.ARC`, lọc theo NAS, công trình, đường dẫn, người dùng, thời gian, hành động.

## Giới hạn kỹ thuật và nguyên tắc
1. Phân biệt ba luồng: (a) audit hoạt động file từ nguồn NAS/giao thức; (b) lịch sử phiên bản từ Synology Drive/Snapshot Replication hoặc nguồn được xác minh; (c) nội dung diff do công cụ riêng tính từ **hai bản tài liệu được cấp phép đọc**.
2. File Station, SMB, WebDAV/RaiDrive, Synology Drive, Synology Office có các mức khả năng/log khác nhau; **không hứa có user/IP/action đủ cho mọi giao thức**. Kiểm chứng thiết bị, DSM, package và quyền từng nguồn.
3. Nếu dùng chung tài khoản thì chỉ khẳng định được tài khoản, không quy kết chắc chắn cá nhân. Metadata như modified_time không chứng minh ai sửa.
4. Không giả định có thể truy hồi lịch sử trước khi bật log/versioning; không hứa số lượng phiên bản cố định cho mọi nguồn.
5. Lưu `observed_at` và `ingested_at`, timezone, original event ID/source, quality, raw action; đánh dấu sự kiện thiếu user/IP và bất định. Dùng checkpoint + dedup để tránh ghi trùng. Báo gap khi collector mất kết nối, log quay vòng hoặc quyền thiếu.
6. Không quét nội dung mọi file mặc định; không thu thập nội dung trong audit DB. Không lưu mật khẩu, SID/token, tài liệu mật hoặc URL ký truy cập trong log.
7. Mọi kiểm tra và thu thập ban đầu **chỉ đọc**; không Apply/Save cấu hình DSM, không bật dịch vụ, không tạo user, không đổi ACL, không bật versioning/snapshot trên NAS nếu chưa có phê duyệt riêng.

## Giao diện
Menu mới: **File Audit & Versions** gồm 4 tab:
- **Hoạt động:** bảng sự kiện với bộ lọc thời gian, NAS, site, công trình, share, WRK/ARC, tài khoản, hành động, source, IP. Cột: thời gian, actor, action, file/path trước/sau, IP, giao thức, nguồn, quality. Drill-down xem event nguyên gốc đã lọc bí mật.
- **Lịch sử phiên bản:** chọn file và nguồn phiên bản; phiên bản/thời gian/kích thước/tác giả (nếu nguồn có), tải xuống có quyền, yêu cầu khôi phục theo luồng duyệt.
- **So sánh:** chọn hai phiên bản; Word: đoạn thêm/xóa; Excel: sheet/cell/value/formula thay đổi, giới hạn dung lượng và định dạng. File mã hóa, định dạng không hỗ trợ, thiếu phiên bản: thông báo rõ. PDF chỉ metadata/hash ở bản đầu, không hứa semantic diff.
- **Tình trạng thu thập:** capability từng NAS/source, lần đồng bộ, log retention/gap, permissions, chất lượng, lỗi và độ trễ.

## Kiến trúc và dữ liệu
- Backend FastAPI; adapter read-only cho nguồn có giao diện hỗ trợ thực tế; collector qua worker riêng với checkpoint, rate limit và backoff; PostgreSQL. Không truy vấn API ẩn hoặc bỏ qua TLS.
- Mô hình: `FileAuditSource(device_id,kind,capability,status)`, `FileEvent(device_id,source_id,event_key,actor,action,path_before,path_after,share,ip,protocol,event_time,ingested_at,quality,raw_ref)`, `CollectionCursor`, `CollectionGap`, `FileVersionRef(device_id,source,stable_file_ref,version_ref,observed_at,size,hash_if_available)`, `CompareJob` (chỉ lưu diff có kiểm soát, TTL), `RestoreRequest` (duyệt).
- Dùng khóa tenant/site/NAS và kiểm tra RBAC trên mỗi truy vấn; không hiển thị path/sự kiện ngoài quyền. Đường dẫn lưu dạng canonical NAS/share/path và tên hiển thị Unicode, chống traversal. Xuất CSV có kiểm soát và theo dõi việc xuất.
- API dự kiến: `GET /api/v1/devices/{id}/file-audit/capabilities`, `GET /api/v1/file-events`, `GET /api/v1/file-events/{id}`, `GET /api/v1/files/versions`, `POST /api/v1/compare-jobs`; restore write endpoints chỉ thiết kế sau, không mở ở MVP.

## Triển khai theo pha / nghiệm thu
**FA-0 khảo sát chỉ đọc:** xác minh DSM/model/package, SMB/WebDAV/RaiDrive, cấu hình transfer log, Log Center/File Station/Drive/Snapshot; chọn thư mục thử nghiệm được cấp phép, kiểm tra loại event thật và khả năng giữ log. Kết quả: ma trận nguồn/capability/evidence; mỗi ô là verified/unverified/unsupported.
**FA-1 MVP audit chỉ đọc:** ingest từ nguồn đã kiểm chứng, lọc/tìm/export CSV, đánh dấu thiếu dữ liệu, nguồn/timestamp; mock demo trước, integration NAS thử nghiệm sau. Nghiệm thu: tạo/ghi/rename/move/delete bằng tài khoản thử trên từng giao thức *được cho phép*, đối chiếu DSM, kiểm chứng timezone/dedup/gap, quyền truy cập.
**FA-2 versions:** đọc listing và tải phiên bản qua nguồn hỗ trợ có xác thực; snapshot/Drive không phải mặc định cho mọi share. Restore yêu cầu RBAC, approval, kiểm tra trạng thái file trước/sau, kế hoạch rollback, chỉ thử trên file test.
**FA-3 compare Word/Excel:** so sánh hai phiên bản theo định dạng, report thay đổi; test formula/value, macro, merged cell, track changes, file lớn và dữ liệu nhạy cảm. Xử lý server cô lập và xóa file tạm sau TTL.

## Chính sách WRK/ARC đề xuất (không phải cấu hình đã áp dụng)
- `1.WRK`: ưu tiên lịch sử ghi/đổi tên/xóa và phiên bản tài liệu có tần suất sửa cao.
- `2.ARC`: ưu tiên theo dõi bất thường sửa/xóa/move và kiểm soát phiên bản/snapshot/retention chặt; cân nhắc tính bất biến theo chính sách.
- Không bật log mọi lệnh read trên hàng chục nghìn folder nếu chưa thử tải và dung lượng. Retention, cảnh báo, phân quyền xem log, encryption, backup và pháp lý cần chốt với đơn vị quản lý dữ liệu.

## Backlog đề xuất
- [ ] FA-001 ma trận capability theo thiết bị, DSM, package, giao thức.
- [ ] FA-002 mock event fixtures và UI 4 tab (ghi rõ dữ liệu giả).
- [ ] FA-003 schema/migration và API search phân trang, RBAC.
- [ ] FA-004 adapter source được hỗ trợ, cursor/retention/gap, integration tests.
- [ ] FA-005 version adapter cho nguồn đã kiểm chứng.
- [ ] FA-006 Word/Excel diff sandbox + quy trình xóa file tạm.
- [ ] FA-007 phê duyệt restore và kiểm thử an toàn trên file thử nghiệm.

**Không có thay đổi nào được thực hiện trên NAS khi bổ sung tài liệu này.**
