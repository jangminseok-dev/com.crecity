from order.app.use_cases.fee_policy_interactor import FeePolicyInteractor


def test_설정값을_그대로_내려준다():
    policy = FeePolicyInteractor(
        brand_fee_percent=10,
        creator_fee_percent=10,
        withdrawal_tax_permille=33,
        response_deadline_hours=72,
    ).get_policy()

    assert policy.brand_fee_percent == 10
    assert policy.creator_fee_percent == 10
    assert policy.withdrawal_tax_permille == 33
    assert policy.response_deadline_hours == 72


def test_요율이_바뀌면_그_값이_나온다():
    # 화면이 숫자를 하드코딩하지 않게 하는 것이 이 슬라이스의 목적이다
    policy = FeePolicyInteractor(
        brand_fee_percent=5,
        creator_fee_percent=15,
        withdrawal_tax_permille=33,
        response_deadline_hours=48,
    ).get_policy()

    assert (policy.brand_fee_percent, policy.creator_fee_percent) == (5, 15)
    assert policy.response_deadline_hours == 48
