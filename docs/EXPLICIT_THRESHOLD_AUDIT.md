# Trích cận số cho các ngưỡng của bản thảo strong thin tree

**Ngày:** 2026-10-08. Đây là phép thế số bảo thủ vào các công thức đã phát biểu trong [bản thảo xây dựng](https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf), Mục 2.4, Proposition 2.5 và Lemma 6.1. Nó **không** kiểm toán độc lập toàn bộ chứng minh Lemma 2.4 từ [bài hình học đi kèm](https://github.com/openai/math/blob/main/preprints/The-strong-thin-tree-conjecture-September-23-2026/paper.pdf). Các cận dưới đây chỉ được dùng nếu các bất đẳng thức nguồn mà chúng dựa vào là đúng.

## 1. Cận đủ `h0 = 2^4096` cho Theorem 2.1

Trong chứng minh Theorem 2.1, đặt `α=h^{-4/5}`, `ε=1/10`, `β=36`, `ρ=1/(2h²)`, `C3=10^4`, `C4=3`. Lemma 2.4(i) định nghĩa

`J=1+ceil(log2(256/α²))`, `C2=128J⁴`, `σ=α/C2`, `L=2+ceil(log2(1/σ))`, `H0=1+ceil(log2(24/(ρσ²)))`, `C1=1024ε^{-2}=102400`.

Đặt `t=log2 h`. Với mọi `t≥4096`, ta có `log2 t≤t/256` (đúng tại 4096 và hiệu `t/256−log2 t` tăng sau đó). Suy ra

- `J≤3t`;
- `C2<2^14 t⁴≤2^{14+t/64}`;
- `L≤2t` và `H0≤4t`.

Các giả thiết số của Lemma 2.4 được đáp ứng:

- `48βC1=176947200<2^28`, còn `σ^ε≤h^{-2/25}=2^{-2t/25}≤2^{-28}`;
- `hσ^{1+2ε}=h^{1/25}/C2^{6/5}≥2^{17t/800−84/5}≥2^18>24C3=240000`;
- `ρ≤1/18`, `β≥36`, `C4=3`, và `C3=10^4≥2(C4+1)+4(C4+2)²`. Điều kiện nút được đánh dấu cũng đúng vì `hρ=1/(2h)≤1/h`.

Trong chứng minh, `c*=C4/(96C3)=1/320000` và `K=384βC1/c*=452984832000000<2^49`. Từ (2.9) và (2.12), sau khi nhân với `h^{31/40}`, cận tỉ số cần kiểm tra là

`2h^{-1/40} + K C2^{11/10} L H0 h^{-29/200}`.

Với các cận trên và `t²≤2^{t/128}`, hạng thứ hai không quá `2^{68−3t/25}`; hạng thứ nhất là `2^{1−t/40}`. Khi `t≥4096`, mỗi hạng không quá `1/4`. Tổng không quá `1/2`, đúng ngưỡng dùng trong Theorem 2.1. Vì thế `h0=2^4096` là một **cận đủ có điều kiện theo Lemma 2.4**, rất xa giá trị tối ưu.

## 2. Cận cho Proposition 2.5

Chứng minh Proposition 2.5 yêu cầu `h=floor(r/2)≥h0` và

`16(h^{-1}+6s h^{-31/40})≤r^{-1/3}` với `s≤r^{1/4}`.

Với `r≥3`, `h≥r/3`, nên vế trái không quá `48r^{-1}+288r^{-21/40}`. Hai hạng lần lượt không quá `r^{-1/3}/2` khi `r^{2/3}≥96` và `r^{23/120}≥576`. Cả hai đúng khi `r≥2^53`: bất đẳng thức thứ hai theo `2^{53·23}>576^{120}`. Do điều kiện `h≥h0` mạnh hơn, một cận đủ là

`r ≥ max(2h0, 2^53) = 2^4097`.

Đây là cận cho **riêng Proposition 2.5**. Các điều kiện bổ sung của Proposition 3.1 được xét tiếp dưới đây.

## 3. Cận có điều kiện cho Proposition 3.1

Đặt `v=log2 r≥4097`, `u=r^{-1/16}`, `κ=1/(m+1)` và `t=κ/32≤1/32`. Lịch ở (3.6) bắt đầu từ `s=1/2` và dừng khi `s≥r^{1/4}`. Vì `ln(1+t)≥t/2`, số bước không quá `2 ln(2r^{1/4})/t+1`. Với `g≤2r^{-1/8}=2u²`, tổng lượng giảm của `Q/r` không quá

`4g ln(2r^{1/4})+2gt ≤ (2v+65/8)u² ≤ 11u`.

Bất đẳng thức cuối dùng `v·2^{-v/16}≤1` và `u≤1` khi `v≥4097`. Suy ra `Q≥(1−11u)r≥3r/4`. Sau khi bỏ baseline và lấy sàn, số cây ít nhất `floor(Q−1)≥Q−2≥(1−12u)r`, vì `2≤ru`. Vì vậy phần **đếm cây** trong Proposition 3.1 cho phép lấy `A=12`, miễn là mỗi bước continuation có nghiệm và các điều kiện của Lemmas 3.2–3.4 thực sự áp dụng.

Các điều kiện “đủ lớn” hiển thị trong Lemma 3.2 đều yếu hơn `r≥2^4097`: `32r^{-1/3}≤r^{-1/8}` khi `r≥2^24`; `Q−2≥floor(r/2)` khi `Q≥3r/4` và `r≥8`; và `r^{-1/3}≤1/10` đủ cho cận thu/lỗ ở trường hợp phân hoạch lớn. Lemma 3.4 nêu các bán kính hữu tỉ theo `P=n+m+2` mà không dùng thêm ngưỡng tuyệt đối trên `r`. Do đó **ứng viên có điều kiện** cho Proposition 3.1 là `r0=2^4097`, `A=12`. Cần kiểm toán độc lập toàn bộ Lemmas 3.2–3.4 và thuật toán LP/ellipsoid trước khi coi đây là giao diện đã xác nhận.

## 4. Cận ký hiệu cho phần làm thưa của Lemma 6.1

Giả sử Proposition 3.1 đã được xác nhận với các hằng số số học `A,r0`, và Lemmas 4.1–5.2 đã có ngưỡng thực thi. Đặt `Cs=2^20`, `B=A+2Cs+6`, và `u=r^{-1/16}`. Các điều kiện

`r≥(8A)^16`, `r≥(16Cs)^8=2^192`, `r≥(2B)^16`, `r≥64`

cho `q≥7r/8`, `εr=Cs r^{-1/8}≤1/16`, `1+4/r≤17/16` và `Bu≤1/2`. Từ (6.5) và phép lấy sàn,

`r'/r ≥ (1−Au)(1/2−Cs u²)/(1+4u¹⁶)−u¹⁶ ≥ (1/2)(1−Bu)`.

Các cận đầu cũng cho `r'≥r/4`, còn thuật toán chặn `r'≤r/2`. Với `ar=(1/2)(1+6Cs u²)` và `Bu≤1/2`, có thể lấy

`C1 = 6Cs + 2B + 12Cs B`

để được `ar/(r'/r)≤1+C1u`. Với ứng viên `A=12`, ta tính `B=2097170` và `C1=26388516044836`. Khi đó `2^4097` lớn hơn cả bốn ngưỡng đại số hiển thị ở đầu mục này.

## 5. Kiểm tra ngưỡng trong Lemmas 4.1, 5.2 và Appendix A

**Lemma 4.1.** Ngưỡng tuyệt đối chỉ xuất hiện trong các cận chuẩn hóa. Với `r≥2` và `r/2≤q≤r`, hệ số nhiễu `δ=1/(100r²)` cho

`[(1+δ)/(1−δ)](1/q+3/r²)≤1/q+4/r²≤(1+4/r)/q`.

Bất đẳng thức cuối dùng `q≤r`. Độ giảm ở mỗi vòng gradient và cận số vòng của chứng minh không đòi `r` lớn thêm: vì bước không dừng giảm ít nhất `1/((M+1)r⁴)` và khoảng cách hàm mục tiêu ban đầu không quá `n ln(2M)`, có thể chặn số vòng bằng `ceil(n(M+1)r⁴ ln(2M))`. Một cận nguyên thô là `2nM(M+1)r⁴`, nhờ `ln(2M)≤2M`. Việc tính gradient gần đúng vẫn cần quy trình precision hữu tỉ của bổ đề; cận vòng không tự cài quy trình ấy.

**Lemma 5.2.** Với `r≥2`, `q≥r/2`,

`r^{-1/4}+(1+4/r)/q≤5r^{-1/4}`.

Sai số cột `1/(1000|B|r)` cho `Σ⪯3I/4` và `∥ae∥²≤3r^{-1/4}` theo (5.4)–(5.5). Cột padding có chuẩn bình phương không quá `1/(2r²)≤3r^{-1/4}`, nên `Δ≤3r^{-1/4}`. Từ `T≤2^16√Δ` và sai số `2/(100r)`, ta có `4T+2/(100r)≤2^20 r^{-1/8}`. Các điều kiện này đều yếu hơn `r≥2^4097`.

**Appendix A.** Theorem A.1 nhận các ma trận hữu tỉ hạng tối đa một và cho hằng số 40; phát biểu và thuật toán của nó không có tham số `r`. Các tham số trong chứng minh phụ thuộc kích thước ma trận và độ dài bit đầu vào, nên Appendix A không tạo thêm ngưỡng tuyệt đối trên `r`. Đây là kiểm tra **giao diện và điều kiện ngưỡng**; tính đúng của toàn bộ thuật toán ký dấu và oracle SDP hữu tỉ chưa được chứng minh độc lập trong repo.

Như vậy có thể dùng **ứng viên có điều kiện** `R0=2^4097`, nếu chấp nhận các Lemmas 2.4, 3.2–3.4, 4.1, 5.2 và Theorem A.1 như bản thảo phát biểu.

## 6. Cận cuối cùng có điều kiện

Với `R0=2^4097` và `C1=26388516044836<2^45`, tổng mất mát trong Mục 6 không quá `C1 R0^{-1/16}/(1−2^{-1/16})`. Bernoulli cho `1−2^{-1/16}>1/32`, nên số mũ này nhỏ hơn `32·2^45·2^{-256}=2^{-206}<1/2`. Dùng `exp(x)<2` khi `x<1/2`, cùng `rinit≥k/3` và hệ số 2 của nén bội số, một hằng số bảo thủ là

`C_binary = 12·2^4097`.

Đây là cận **suy ra có điều kiện từ các bổ đề nguồn**, không phải bảo đảm đã được mã hóa và kiểm chứng đầu cuối. Nó khổng lồ và không hữu ích để dự đoán chất lượng thực nghiệm. `scripts/check_thresholds.py` kiểm tra các bất đẳng thức nguyên ở đầu mút; lập luận đơn điệu cho mọi `h,r` lớn hơn nằm trong tài liệu này. Việc còn lại là kiểm toán độc lập các bổ đề nguồn và cài LP, khung vector, ký dấu, làm thưa với chứng chỉ chính xác.
