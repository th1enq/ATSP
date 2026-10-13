# Kế hoạch kiểm toán và cài đặt strong thin tree thời gian đa thức

**Đường chạy lớn đã bổ sung:** chế độ mặc định dùng chứng chỉ PSD và cận
support, không liệt kê mọi lát cắt hay gọi đối chứng vét cạn. Đã chạy mẫu
20 và 32 đỉnh từ HK đến tour AKS; xem `SCALABLE_PIPELINE_2026-10-11.md`.
Giới hạn 16 đỉnh trong ghi chú cũ chỉ còn áp dụng cho phép đo mọi lát cắt
được bật bằng `--exact-small`. Bảo đảm strong thin tree phổ quát vẫn còn mở.

**Ngày lập:** 2026-10-08  
**Đích:** từ nghiệm Held–Karp hữu tỉ, xây dựng cây bao có hỗ trợ với bảo đảm mỏng hằng số bằng thuật toán đa thức thực sự, rồi chuyển cây sang pipeline AKS. Nguồn thuật toán là [bài xây dựng strong thin tree](https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf); điều kiện giao tiếp với AKS theo [An–Kleinberg–Shmoys](https://arxiv.org/pdf/2012.14233).

**Cập nhật 2026-10-11:** `scripts/experimental_tree.py` đã nối nén HK, packing, nhiều vòng làm thưa, chiếu cây và lệnh C++ `round-supplied-tree` sang AKS. Đường thực nghiệm thử các shortcut `X=c L_H`, cân bằng khung hữu tỉ có giới hạn và hai thứ tự ký dấu xác định; mọi đầu ra đều được kiểm tra PSD, packing và tất cả lát cắt. Bộ xác minh JSON không chạy lại thuật toán tìm khung, ký dấu hay packing. Đây là bản thực nghiệm cho `n<=16`, có thể dừng ở packing cuối khi điều kiện bước tiếp theo không đạt; chưa phải backend phổ quát của Theorem 1.1. Xem `EXPERIMENTAL_PIPELINE_2026-10-11.md` và `../results/experimental_tree/summary.csv`.

**Bộ tham chiếu:** `construct-certified` là bộ tham chiếu vét cạn, có chứng chỉ hữu tỉ, giới hạn 10 đỉnh. Nó là oracle kiểm thử cho các mốc dưới đây. Xem `THEORY_AUDIT_2026-10-08.md` và `CONSTRUCTIVE_AUDIT_2026-10-08.md`.

**Cập nhật 2026-10-09:** Mốc 2 có tiền xử lý chính xác `scripts/certify_compress.py`. Mốc 3 có packing và oracle phân hoạch. Mốc 4 có solver ellipsoid hữu tỉ và lịch continuation nhưng chưa xác nhận chạy đầu cuối ở miền tham số khổng lồ của định lý. Mốc 5 có khung, padding, bộ sinh dấu Frobenius và nhánh Appendix A hữu tỉ với oracle SDP, sai phân, hướng cong âm và kiểm tra phổ cuối; thử nghiệm đầu cuối của nhánh Appendix A mới đạt kích thước 1×1. Mốc 6 có một bước làm thưa tự động được chứng nhận trên mẫu nhỏ và có thể chọn `signing_method="appendix_a"`, chưa có vòng lặp và cận hằng số không điều kiện. Mốc 0 chưa qua điều kiện kiểm toán độc lập các bổ đề sâu. Kết quả đo ở `THESIS_EXPERIMENTAL_AUDIT.md`; phạm vi dấu ở `DETERMINISTIC_SIGNING_AUDIT.md`.

**Cập nhật Mốc 3:** `scripts/tree_packing.py` đã cài graphic matroid union cho các bản sao cạnh tường minh, xuất cây bao rời cạnh hoặc phân hoạch cản trở và có lệnh xác minh chứng chỉ. `scripts/weighted_partition_oracle.py` tách chính xác bất đẳng thức phân hoạch có trọng số bằng tối đa `n` min-cut theo [Baiou–Barahona–Mahjoub (2000)](https://www.lamsade.dauphine.fr/~mahjoub/Papers/BBM00.pdf), thay cho LP (3.18) của bản thảo. Nghiệm được đối chiếu với mọi phân hoạch trên 150 đồ thị nhỏ ngẫu nhiên. Hai thành phần Mốc 3 đã có nhưng chưa ghép thành backend xây cây mỏng.

**Cập nhật backend thực thi:** `construct-polynomial-baseline` đã nối kiểm tra HK hữu tỉ bằng min-cut, cây BFS trên support và AKS bằng cận chính xác `beta=min(D,(n-1)/2)`. Nó chạy đa thức trên đầu vào tường minh và vượt giới hạn 10 đỉnh của oracle vét cạn. Vì cận beta phụ thuộc `n` hoặc `D`, đường này chưa đạt điều kiện Mốc 6 về hằng số độc lập đầu vào.

Oracle MST hữu tỉ và bộ đối chứng phân hoạch nhỏ vẫn có trong `scripts/weighted_partition_oracle.py`. Bộ kiểm tra PSD hữu tỉ của Mốc 4 nằm ở `scripts/exact_psd.py`; `scripts/continuation_oracle.py` ghép PSD, ràng buộc vô hướng và phân hoạch thành bộ tách siêu phẳng hữu tỉ cho một bước (3.8), (3.14)–(3.16). `scripts/continuation_state.py` tính điện trở hiệu dụng và kiểm tra packing. `scripts/rational_ellipsoid.py` làm tròn tâm/ma trận về lưới nhị phân sau mỗi phép cắt, có nới miền bao để giữ tập khả thi. `scripts/continuation_solver.py` dùng oracle này sinh response, lặp lịch và packing cạnh điện trở thấp. Định lý bán kính trong của Lemma 3.4 chưa được kiểm toán độc lập và kiểm thử mới bao phủ bước nhỏ.

`scripts/exact_psd.py` đã thêm phân rã chính xác ma trận PSD hữu tỉ thành tổng các tích ngoài hạng một theo Lemma 5.1; kiểm thử dựng lại ma trận đúng từng phần tử. Đây là tiền đề cho padding của Lemma 5.2, chưa phải thuật toán ký dấu Appendix A.

`scripts/rational_frame.py` tính trọng số hữu tỉ dương bằng gradient (4.2)–(4.4), kiểm tra leverage score chính xác và xấp xỉ khung trắng hóa với cận sai số. `scripts/signing_padding.py` dựng phần bù PSD và padding để tổng tích ngoài bằng ma trận đơn vị đúng từng phần tử. `scripts/deterministic_signing.py` có hai nhánh: Frobenius nhanh và Appendix A qua `appendix_a_potential.py`, `appendix_a_value_oracle.py`, `appendix_a_signing.py`. `scripts/verified_sparsification.py` dùng chúng để tự sinh một tập cạnh rồi kiểm tra chứng chỉ nón shortcut, bất đẳng thức phổ và packing `r'`. Nhánh Appendix A đã nối vào một bước làm thưa nhưng cần thử nghiệm qua nhánh cong âm và kiểm toán độc lập chứng minh độ chính xác, xem `DETERMINISTIC_SIGNING_AUDIT.md`.

Kiểm toán ngưỡng bổ sung ở `EXPLICIT_THRESHOLD_AUDIT.md` đã suy ra ứng viên có điều kiện `h0=2^4096`, `A=12`, `r0=R0=2^4097`, `C_binary=12·2^4097`. Các cận này dựa vào các bổ đề nguồn chưa được kiểm toán độc lập; các thành phần LP/ma trận/ký dấu đã có bản cài đặt nhưng đường tổng quát chưa được kiểm chứng đầu cuối. Vì vậy Mốc 0 và backend có bảo đảm hằng số phổ quát chưa qua điều kiện hoàn thành.

## Quy tắc xác nhận

- **Chứng minh:** mỗi mốc có phát biểu bất biến, giả thiết, chứng minh hoặc tham chiếu tới bổ đề đã kiểm toán. Kiểm thử không thay thế chứng minh.
- **Kiểm tra máy:** đầu ra đi kèm chứng chỉ số nguyên/hữu tỉ hoặc ma trận PSD có thể kiểm tra lại độc lập khi khả thi.
- **Thực nghiệm:** đối chiếu với bộ vét cạn trên mẫu nhỏ, rồi đo thời gian và độ dài bit trên mẫu lớn hơn. Đồ thị ngẫu nhiên chỉ cho bằng chứng thực nghiệm.
- **Tên gọi:** chỉ gắn nhãn `strong_thin_tree_polynomial` khi mọi đường thực thi của backend mới đều dùng thuật toán đa thức đã kiểm toán, không dùng vét cạn hay heuristic làm đường dự phòng.

## Mốc 0 — Khóa đặc tả và kiểm toán nguồn

1. Lập đồ thị phụ thuộc của Theorem 1.1: Theorem 2.1/Proposition 2.5 → Proposition 3.1/Lemmas 3.2–3.4 → Lemma 4.1 → Lemma 5.2/Appendix A → Lemma 6.1 → Theorem 1.1.
2. Với từng bổ đề, ghi đầu vào, đầu ra, bất biến, phép toán số học, yêu cầu độ chính xác và tài liệu chứng minh. Kiểm tra nguồn của các phép toán được viện dẫn như matroid partition, ellipsoid và matrix signing; xác định các đoạn Lean nào thực sự chứng minh phát biểu cần dùng.
3. Trích xuất các ngưỡng `h0`, `r0`, `R0` và hằng số `A`, `Cs`, `C1`, hoặc thay bằng giá trị bảo thủ được chứng minh. Tính một `C` chung cho đồ thị tường minh và bội số nhị phân.

**Điều kiện qua mốc:** có bảng kiểm toán từng phụ thuộc, không còn phép gọi “đủ lớn” chưa được lượng hóa trong mã, và có phát biểu bảo đảm số học đầu ra. Nếu một bổ đề nguồn không xác nhận được, ghi rõ chỗ hở trước khi xây backend phụ thuộc vào nó.

## Mốc 1 — Lớp dữ liệu chính xác và bộ oracle tham chiếu

1. Thay giới hạn `uint64_t` của đường chứng chỉ bằng số nguyên/hữu tỉ có độ dài tùy ý. Nghiệm Held–Karp phải được kiểm tra bằng tổng bậc và các lát cắt có hướng; đối với đầu vào lớn dùng tách ràng buộc bằng min-cut thay vì liệt kê mọi tập con.
2. Giữ backend vét cạn hiện tại làm oracle cho `n <= 10`; mở rộng bộ ca gồm chu trình nguyên, witness 6 đỉnh, họ tách đỉnh, nghiệm phân số có mẫu số lớn và các chứng chỉ sai có chủ đích.
3. Định nghĩa một giao diện thống nhất: `RationalHK -> BinaryMultigraph -> StrongThinTree -> AKS`, trong đó từng bước mang dữ liệu để kiểm tra giả thiết.

**Điều kiện qua mốc:** đầu vào hữu tỉ tùy độ dài bit không bị làm tròn trong các bất biến; oracle nhỏ phát hiện chứng chỉ sai và trả đúng hệ số mỏng tối ưu khi hoàn tất tìm kiếm.

## Mốc 2 — Nén bội số nhị phân theo Mục 6

Với bội số `c_uv` và độ kết nối `k`, cài đặt `c'_uv=min(c_uv,k)` và `a_uv=floor(2n² c'_uv/k)` mà không mở rộng `c_uv` bản sao. Kiểm tra các kết luận của bài: đồ thị tường minh có ít hơn `n^4` cạnh, mọi lát cắt có ít nhất `n²` cạnh, và tải lát cắt không vượt `(2n²/k)` lần tải ban đầu.

**Kiểm chứng:** trên mẫu nhỏ, liệt kê mọi lát cắt và đối chiếu trực tiếp; trên mẫu lớn, kiểm tra cận dưới min-cut và chứng chỉ phép tính theo từng cặp đỉnh. So sánh cây thu được sau khi chiếu về support ban đầu với oracle nhỏ.

**Điều kiện qua mốc:** mọi phép tính dùng số nguyên chính xác; bộ nén xử lý các trường hợp `c_uv >> k`, nhiều cạnh song song và bội số có hàng nghìn bit mà không cấp phát theo giá trị bội số.

## Mốc 3 — Packing cây và tách ràng buộc chính xác

1. Cài đặt hoặc tích hợp graphic matroid partition để tìm `r` cây bao không chung cạnh trên đa đồ thị tường minh; chứng chỉ đầu ra là danh sách các cây, kiểm tra tính rời nhau và bao trùm.
2. Cài đặt oracle tách bất đẳng thức phân hoạch của Lemma 3.3 theo bài toán MST/LP chính xác. Trên đồ thị nhỏ, so sánh với liệt kê phân hoạch.
3. Đối chiếu số cây packing tối đa với nghiệm vét cạn ở kích thước rất nhỏ.

**Điều kiện qua mốc:** trả đúng quyết định packing và chứng chỉ; số phép toán và độ dài bit được chặn đa thức theo đầu vào tường minh.

## Mốc 4 — Các thành phần ma trận của Proposition 3.1

1. Cài đặt biểu diễn ma trận trên `1⊥`, phép kiểm tra PSD hữu tỉ, tách ràng buộc của chương trình lồi và quy trình ellipsoid với bán kính trong/ngoài của Lemma 3.4.
2. Cài đặt lịch continuation và kiểm tra tại mỗi bước `X` thuộc miền cho phép, điện trở cạnh, bất đẳng thức phân hoạch và độ dài bit.
3. Đối chiếu các bất biến trên mẫu nhỏ bằng tính toán chính xác; dùng tính toán số thực chỉ để chẩn đoán và so tốc độ.

**Điều kiện qua mốc:** Proposition 3.1 xuất được ma trận hữu tỉ và packing cây điện trở thấp, có chứng chỉ kiểm tra lại; mọi giới hạn độ chính xác được lấy từ chứng minh đã qua Mốc 0.

## Mốc 5 — Khung vector, ký dấu và một bước làm thưa

1. Cài đặt Lemma 4.1: khung vector giữ hạng incidence, chuẩn hóa và sai số xấp xỉ với cận hữu tỉ.
2. Cài đặt Lemma 5.2 và Appendix A: thuật toán ký dấu xác định, các phép thử PSD chính xác và giới hạn số bước/độ dài bit.
3. Ghép thành Lemma 6.1. Sau mỗi bước, kiểm tra tập cạnh mới, packing `r'`, chứng chỉ ma trận và bất đẳng thức tải lát cắt suy ra từ chứng chỉ. Với `n` nhỏ, còn kiểm tra mọi lát cắt trực tiếp.

**Điều kiện qua mốc:** chạy được một bước làm thưa với bất biến đã chứng nhận và `r/4 <= r' <= r/2`. Không nhận một lựa chọn dấu ngẫu nhiên/heuristic làm bằng chứng cho Lemma 5.2.

## Mốc 6 — Lặp đến cây và nối AKS

1. Lặp Lemma 6.1 đến khi số cây packing thấp hơn ngưỡng cố định; trả cây bao cuối và chiếu cạnh về support `z`.
2. Ghi chứng chỉ của từng vòng và cận tổng hợp `C/k`. Dùng cận `C` đã cố định ở Mốc 0 để suy ra `beta <= C/2` cho Held–Karp.
3. Chuyển cây và nghiệm Held–Karp hữu tỉ sang AKS; tính mọi phép làm tròn capacity và `ceil(4 beta)` chính xác.

**Điều kiện qua mốc:** toàn bộ đường `HK -> tree -> AKS` chạy không qua vét cạn, báo bảo đảm số học cụ thể, và mỗi bước có thể kiểm tra lại. Trên đồ thị nhỏ, kết quả được đối chiếu với oracle tối ưu hiện có.

## Mốc 7 — Kiểm chứng thực nghiệm và công bố phạm vi

- **Đúng đắn:** các ca hồi quy cũ, đồ thị có nhiều lát cắt sát `k`, bội số rất lớn, mẫu số hữu tỉ lớn, và trường hợp nhỏ/ngưỡng của mọi nhánh thuật toán.
- **Độ phức tạp:** đo thời gian, bộ nhớ, số lần gọi oracle và độ dài bit lớn nhất theo `n`, số cặp cạnh và độ dài bit đầu vào. Đo lường chỉ hỗ trợ đánh giá thực tiễn; chứng minh đa thức nằm ở các cận của từng mốc.
- **Chất lượng:** ghi `beta`, số lần thăm đỉnh, bottleneck tạo ra và tối ưu chính xác khi kích thước cho phép. So sánh cùng bộ instance với backend vét cạn và các heuristic hiện có.
- **Báo cáo:** tách rõ bảo đảm lý thuyết, chứng chỉ kiểm tra, kết quả thực nghiệm, và các giả thiết nguồn còn chờ thẩm định độc lập.

## Thứ tự thực hiện ngay

Bắt đầu bằng **Mốc 0 và Mốc 1**, rồi triển khai **Mốc 2**. Mốc 0 quyết định tham số và phép toán chính xác cần có; Mốc 1 tạo cơ sở kiểm thử; Mốc 2 là phần đầu tiên của thuật toán nguồn có thể xác nhận độc lập. Chỉ sau ba mốc này mới chọn công cụ cụ thể cho tối ưu ma trận và ký dấu.
